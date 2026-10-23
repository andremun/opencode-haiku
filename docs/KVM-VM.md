# Persistent KVM Haiku VM (cardless)

Built 15 October 2026 on `uld-jvnhw22`, a Dell Precision T7610 (DMI product
name) with two installed Xeon E5-2620 v2 (Ivy Bridge, AVX, no AVX2). This is
the T7610 test platform of `docs/DEVELOP.md`, with the CPUs that are
actually installed. No GPU, host driver, host sudo or existing host
LLM service was touched. A result from this VM is a **CPU** result and says
nothing about K40c compute support.

## What exists

| Item | Value |
|---|---|
| Disk | `vm/system.qcow2`, 32 GiB virtual (about 3.3 GiB used), GPT |
| Partitions | `esp` 256 MiB FAT32 (EFI system data) and `HaikuVM` 31.75 GiB BFS |
| Guest | Haiku hrev60207 x86_64 anyboot nightly, `R1~beta6+development`, kernel built 5 Oct 2026 |
| Install ISO | `cache/haiku-master-hrev60207-x86_64-anyboot.iso`, SHA-256 `4cd0765e078414681cd64b1063f5d6c0d19dc6daa51c142c544cc4d614260e35` |
| Hypervisor | QEMU 6.2.0, `-accel kvm -cpu host`, q35, OVMF UEFI (`vm/vars.fd`) |
| Resources | 2 vCPU, 8 GiB RAM (host: 2 x 6 cores / 24 threads, 62 GiB, shared with a host LLM service) |
| Devices | IDE disk, e1000 user-mode network, xHCI + USB tablet, std VGA, no display window |
| Control | QEMU monitor and QMP on unix sockets under `/tmp` (`haiku-k40c tools/haiku/app_vm.py`), saved launch command in `vm/launch.json` |
| Guest CPU as seen by Haiku | `Intel Xeon E5-2620 v2`: SSE3, SSSE3, SSE4.1, SSE4.2, POPCNT, AES, PCLMUL, AVX, F16C. **No AVX2, FMA or BMI2** |
| Guest software | Node 24.21.0-1, GCC 13.3.0, CMake 4.4.4, git 2.54.0, ripgrep 14.0.1, Rust 1.94.1-1 (`rust_bin`), `nodejs24_devel`, `libffi_devel` (`logs/` copy: `results/20261015-t7610-kvm/guest-packages.txt`) |

The VM uses **explicit KVM**. `haiku-k40c tools/haiku/app_vm.py start --kvm` fails if KVM is
unavailable; there is no silent fall back to TCG. The earlier development VM (TCG,
`qemu64`, 2 vCPU, 4 or 8 GiB) is the baseline in `docs/STATUS.md`.

## Commands

```sh
python3 haiku-k40c tools/haiku/app_vm.py start --installed --kvm     # boot the installed disk (8 GiB, KVM)
python3 haiku-k40c tools/haiku/app_vm.py screen                      # writes vm/screen.png (2048x2048)
python3 haiku-k40c tools/haiku/app_vm.py type 'text'                 # type a line (US keymap only)
python3 haiku-k40c tools/haiku/app_vm.py key ctrl-x                  # one key or chord
python3 haiku-k40c tools/haiku/app_vm.py click X,Y                   # coordinates in vm/screen.ppm pixels
python3 haiku-k40c tools/haiku/app_vm.py stop                        # quit QEMU (no ACPI shutdown)
python3 haiku-k40c tools/haiku/transfer_server.py                    # localhost transfer service (separate host terminal)
```

Practical notes:

- `vm/screen.png` may be displayed scaled. Click coordinates are in the
  **ppm** pixel frame: multiply coordinates read from a ~1932 px wide display
  by about 1.06. Take a fresh `screen` after any resolution change, because
  `click` reads the size of the last screenshot.
- The first boot after an install may show a black screen. That is the Haiku
  screen blanker: press a key (`key shift`).
- `start` without `--installed` attaches the install ISO; use it only to
  install or repair. Remove `vm/boot.qcow2` before reusing an install session.
- `vm/transfer.log`, `vm/serial.log` and `logs/` are ignored by Git.

## How it was installed (reproducible)

1. `python3 haiku-k40c tools/haiku/app_vm.py start --kvm` (installer boots from the ISO).
2. Installer, then **Set up partitions**: initialise the 32 GiB disk with the
   **GUID Partition Map**. Create a **256 MiB** partition of type *EFI system
   data* and format it FAT32 (`esp`). Create the rest as *Be File System* and
   format it BFS (`HaikuVM`, block size 2048, query support on).
3. Install onto `HaikuVM`.
4. **The nightly installer does not copy the UEFI loader onto the new ESP.**
   Without it UEFI drops to the shell. Fix, still in the live ISO session:
   `cp -r "/haiku esp/"* /esp/` (after `mountvolume -all`). This puts
   `EFI/BOOT/BOOTX64.EFI` (and `KEYS/`) on the new ESP. Shut down, remove the
   ISO, boot with `--installed`.
   A first attempt with only a BFS partition booted to the UEFI shell and was
   discarded.

## Remote execution without SSH

The guest has no SSH daemon (earlier approval review rejected one). Work is
driven by a localhost job runner instead:

- `haiku-k40c tools/haiku/transfer_server.py` serves `share/` on `127.0.0.1:18080`; the guest
  reaches it at `http://10.0.2.2:18080/`. PUT requests whose name starts
  with `job` are stored under `logs/`; other names still go to `results/`.
- `tests/acceptance/vm/agent.sh` (copy it to `share/` to serve it) runs in a guest Terminal (`curl http://10.0.2.2:18080/agent.sh -o /tmp/agent.sh; sh /tmp/agent.sh N &`).
  It fetches `jobN.sh`, runs it and uploads `jobN.out`.
- `haiku-k40c tools/haiku/job.sh N 'commands' [timeout_s]` writes `share/jobN.sh` and prints the
  output, returning the guest exit code. Use a fresh N each time; reused numbers
  are rejected. Request/result publication is atomic. A host wait timeout
  returns 124 and does not cancel guest execution. The agent is **not** started automatically at boot.
- Long work: start it with `nohup sh script > log 2>&1 &` inside a job and poll.

No transfer service or guest process is exposed beyond localhost.

## Capabilities and limits

| Capability | State |
|---|---|
| Persistent disk, reboot-safe | Yes. State in `vm/system.qcow2` and `vm/vars.fd`; keep both together |
| KVM acceleration | Yes, verified (`-accel kvm`, `-cpu host`) |
| Native build tools in the guest | Yes: g++/cmake (llama.cpp), Node and node-gyp (Koffi, node-pty), Rust (PTY daemon) |
| Network to the Internet from the guest | Yes (HaikuPorts, GitHub, Hugging Face) through QEMU user networking |
| Host to guest file transfer | HTTP over localhost (above) |
| Guest to host SSH | No |
| GPU, passthrough, CUDA | No, by rule |
| Parallel jobs | 2 vCPUs: builds and model requests compete. Run measurements alone |
| Boot of a Haiku guest with the K40c | Out of scope here (see the `haiku-k40c` repository) |

Disk use after the work in `docs/T7610-KVM-RESULTS-20261015.md`: about 3.3 GiB.

## Scripts used for the 2026-10-15 run (then `tools/kvm-run/`, now `tests/acceptance/vm/`)

Copy them into `share/` (ignored by Git) to serve them to the guest, then run
each with a job (the full-log/status corrections added after the original
run require a native rerun): `agent.sh` (job runner), `llama.sh` (fetch the repo, patch and
build llama.cpp), `model.sh`, `native.sh` (Koffi, clipboard, node-pty, SDKs),
`pty.sh` (daemon build, tests, Clippy), `inf.sh` (cold/warm/cold controls),
`api.sh` (file/shell/session, browser PTY and persistent terminal API tests),
`services.sh` (model and OpenCode backend; preserves existing configuration,
otherwise generates a private local password and refuses duplicate listeners),
`pair.sh` (browser pairing link), `coding.sh`. They assume the guest paths
`/boot/home/...` used in the T7610 guide. Host side: `share/opencode-haiku-src.tar.gz`
(repository files), `share/guest-stage.tar.gz` (patched Koffi, node-pty, PTY
daemon sources), `share/libghostty-vt.a` and the runtime archive are generated
and ignored.

## State at handoff

The VM was shut down cleanly from inside Haiku; `qemu-img check` reports no
errors. Nothing starts automatically: boot it, open a Terminal, start the job
agent, and start the model and OpenCode servers with `services.sh` as needed.
The localhost transfer service was stopped. Experimental renderer copy for the
terminal pane lives in the guest at `/boot/home/opencode-haiku-exp-ghostty`.
