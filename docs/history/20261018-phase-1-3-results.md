# Continuation phases 1 to 3: results

18 October 2026 (Australia/Melbourne). Cardless only: the persistent KVM Haiku VM
([KVM-VM.md](../KVM-VM.md)), no GPU, no host sudo, no change to any host LLM service. Evidence:
`haiku-k40c results/20261018-esc001-native-load/` (phase 1) and `results/20261018-phase123/`
(phases 2 and 3). A CPU or cardless result is not GPU evidence.

## Dependency question

Phases 1 to 3 do not depend on the driver's A3 VBIOS inventory or on later driver work (devinit
executor, board operations, card experiments). Phase 1 needs only the cross compiler, the guest's
exact kernel and a working cardless guest; A3 is also already accepted (independent rework,
2026-10-16).

## Phase 1: native link and load of the driver probes (ESC-001)

ESC-001 (driver repository) stopped after three emulated (TCG) guests failed to reach the test job.
Fix applied, using that escalation's own recommendation (a known-working cardless guest):

| Step | Result |
|---|---|
| `cardless_run.py --base <persistent VM disk> --cpus 2 --kvm` (disposable overlay, no GPU) | `pass` in 44.75 s; exported kernel and environment |
| Guest | `Haiku shredder R1~beta6+development hrev60207 Oct 5 2026 x86_64` |
| Exported `kernel_x86_64` SHA-256 | `2da9a5b98719b40a61893836fb9c9e393e92e44f470e8af2024e76d50e2d2c62` (2,306,657 bytes) |
| Existing `~/haiku-cross/lib/kernel_x86_64` | **byte-identical** (`cmp`), so the kernel used for linking matches the running guest |
| `prepare_cross.sh --check`, `build_backend.sh` with `HAIKU_CROSS=$HOME/haiku-cross` | pinned cross compiler ready; `k40_cardless_probe` and `k40_identity_probe` link (`--no-undefined`) |
| `cardless_run.py --driver build/haiku/k40_cardless_probe --cpus 2 --kvm` | `pass` in 49.6 s, `job.exit` 0, `K40-CARDLESS-BEGIN/END` markers, `k40_os: PASS native OS mechanics only` (host allocation, emulated-VGA read-only MMIO id `0xb0c5`), no panic |

Probe hashes: cardless `8e36442a…`, identity `5b9f30ea…` (`hashes.txt`). The identity probe was
built only; it was not run. The VM's base disk was not modified (`qemu-img check` clean).
This satisfies the ABC1 acceptance conditions for native link/load of the OS-mechanics probe. It
says nothing about the K40c: real BAR mapping, DMA, VRAM and firmware behaviour remain unverified.
Driver-repository edits: only an uncommitted resolution note in `escalations/ESC-001.md`; no
scripts, QEMU command lines or tracked sources changed there.

## Phase 2: Ivy Bridge, OpenMP off, as the Haiku CPU default

Adopted in this repository: `tools/kvm-run/services.sh` defaults to `ivybridge` (and refuses clearly
if that build is absent); `docs/T7610-HAIKU-SETUP.md` section 5 documents it. The batch default is
unchanged (128/32): in the 3-repetition session the prompt rates for 128/32 and 512/128 were
indistinguishable (10.8 and 10.1 tokens/s).

| Check | Result |
|---|---|
| Stories15M (pinned, SHA-256 `6151b192…`) greedy 32-token completion through `llama-server`, compared with the recorded Linux CPU reference text | **exact match** for baseline, ivybridge, production-noomp and production |
| Generation rate on that tiny model (tokens/s) | baseline 180, ivybridge 361, production-noomp 374, production (OpenMP) 52 |
| OpenCode `run` exchange against the local model, 223-token prompt | ivybridge **40 s** (prompt 7.9 tokens/s); baseline **165 s** (prompt 1.4 tokens/s) |

Caveats: the Stories timings overlapped a host-side Zig build, so they are indicative, not a
benchmark; the 7x OpenMP slowdown agrees with the earlier 3-repetition Qwen3 benchmark (decode 4.1
against 6.7 tokens/s). The Qwen3.6-35B production graph capture was not attempted: it does not fit
the 8 GiB guest and would be a host-side task. More than 2 vCPUs were not measured; the guest is
fixed at 2 vCPU. The deployed `llm-server` binary was not run (it initialises both K40c cards).
`haiku-k40c-llm` build scripts still use the SSE2 flags; they were not changed because their recorded
evidence was produced with those flags.

## Phase 3: OpenCode port

| Item | Result |
|---|---|
| Browser terminal panel (WebPositive) on the KVM build | Opens with `/terminal`; shell, UTF-8 output (`WEB_PANE é€`), size 20x47; closed by `exit`, terminal list empty (`screens/browser-terminal-*.png`) |
| TUI terminal resize | window enlarged: pane `stty size` 24x38 to 39x62 (`screens/tui-*resize.png`) |
| TUI quit and relaunch (reconnect) | terminal stayed `running` through the quit (API); after relaunch all earlier output including `RECONNECT_MARKER_42` was restored (`screens/tui-reconnected-2.png`) |
| TUI latency per profile | see Phase 2 (40 s against 165 s) |
| Renderer hash difference (`908b0308…` vs `98c2f036…`) | explained: the build is deterministic from a clean cache (two clean builds identical); the archived file differs from a clean build only in 31 bytes, an embedded Zig cache directory name (`renderer-reproducibility.txt`). Same code. The archive hash in the manifests therefore stays valid for that file |
| Cloud runs on more models, variance | **not done**: needs a new key (see [SECRETS.md](../SECRETS.md)) |
| Push to GitHub | **not done**: user step (no credentials here) |

Not covered: TUI session reconnect from a second concurrent client, a paid model, multiple vCPU
scaling, anything about the K40c. The VM is shut down cleanly; the transfer service is stopped.
