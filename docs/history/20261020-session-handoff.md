# Handoff for separate sessions (state on 20 October 2026, Australia/Melbourne)

Written at the end of a long session that ran from 15 October. Each task below can be started in a fresh session using only
this file plus the documents it names. Rules that apply to everything: **a CPU, cardless or host-compiler result is never
evidence that the K40c works under Haiku**; no host sudo; no push without an explicit instruction; no subagents; never
write credentials, keys or pairing links into a repository; read each repository's own `AGENTS.md` before changing it.

## 1. The four repositories (all under `/home/unimelb.edu.au/mariom1/`)

| Name | Path | Remote | State |
|---|---|---|---|
| OpenCode port | `Documents/packages/opencode-haiku` | `andremun/opencode-haiku` | `main` in sync with origin at `7970e38` (plus this handoff commit, local) |
| Driver | `Documents/packages/haiku-k40c` | `andremun/haiku-k40c` | `main`; **1 commit ahead, not pushed**: `231b053` (ESC-001 resolution note) |
| Guest LLM (Haiku llama.cpp) | `Documents/packages/haiku-k40c-llm` | `andremun/haiku-k40c-llm` | `main`; **1 commit ahead, not pushed**: `e0e38fa` (Ivy Bridge profile) |
| Host LLM server (Linux, CUDA) | `llm-server` | none | `main` at `513fad8`, clean, untouched by this session |

Who changed what since 15 October: the driver repository (10 commits, 16 Oct), the host server (3 commits, 15 and 16 Oct) and
three OpenCode commits (`3b13e60`, `27ebd52`, `d648a06`, 15 Oct; plus `7970e38`, 19 Oct) came from outside this session.
Everything else listed here was done in this session and carries the trailer `Co-Authored-By: Claude Sonnet 5.5`.

## 2. What this session did (by repository)

**OpenCode port** (about 17 commits of mine, newest first): production-matching and no-OpenMP CPU builds; Haiku.5 validated on a
persistent KVM Haiku VM (54 daemon tests, API probes, TUI terminal pane, clipboard, browser terminal, resize and reconnect); audit
review (8 fixes, 2 wrong claims, 4 left unchanged: `docs/AUDIT-2026-10-18-DISPOSITION.md`); a real CSV coding task solved by a free
cloud model through the port in the VM (`docs/FREE-MODELS-AND-CLOUD-TASK.md`); key-handling tooling (`docs/SECRETS.md`); Ivy Bridge
(OpenMP off) made the Haiku default profile; host capability report; GPU-free Clang 23 against nvcc 11.4 comparison; community
llama.cpp comparison; full Clang-built `libggml-cuda`; **two on-card comparisons** (section 3, task A: Clang against nvcc, then the Clang fixes and hybrid libraries).

**Driver:** ESC-001 (native guests stalled) was unblocked: the persistent KVM guest exported its kernel (SHA-256 `2da9a5b9…`,
byte-identical to `~/haiku-cross/lib/kernel_x86_64`), both probes link, the cardless probe loads with `k40_os: PASS`. Evidence:
`opencode-haiku/results/t7610-20261018-driver-native/`. Only the note `escalations/ESC-001.md` was changed there.

**Guest LLM:** `tools/build_guest.sh` and `share/build_guest.sh` (identical) now default to the Ivy Bridge profile (SSE4.2, AVX,
F16C on; AVX2, FMA, BMI2, OpenMP off) with a CPU feature check and fallback to the SSE2 baseline; `docs/REPRODUCE.md` and
`docs/STATUS.md` updated. The host Makefile reference flags are unchanged. The graph capture was explicitly **not** attempted.

**Host server:** nothing edited. On 20 October the service `llama-server-one.service` was stopped 08:56 and started again 10:40
for the card comparison (new PID 937821, healthy). Note: the restarted process loads the binary now on disk (rebuilt 16 Oct 13:30);
the earlier process predated that rebuild.

## 3. Task cards

### A. Clang against nvcc on the K40c: follow-up (OpenCode repo, needs card authorisation)
- **Read first:** `docs/KEPLER-HYBRID-20261020.md` (newest), `docs/KEPLER-CARD-COMPARISON-20261019.md`, `docs/KEPLER-LLVM-STATIC-20261018.md`, `docs/HOST-CAPABILITIES-20261018.md`.
- **State (20 Oct, second card run done):** a hybrid library (24 files from Clang: `mmvq.cu`, `softmax.cu`, `mmq.cu` plus the 21 MMQ instances; the rest from nvcc)
  passes all tested operations (flash attention 2832/2832) and gives about +5% token generation on Qwen3.5-9B (9.57 to 10.05 tokens/s), prompt unchanged; matrix kernels
  about 9% (MUL_MAT) and 4% (MUL_MAT_ID) faster in median. The full Clang build still fails attention (about 360 to 418 of 2,832 cases give NaN; `-fno-finite-math-only` did not help,
  dropping `-ffast-math` helped slightly). Not deployed; the service uses the nvcc library.
- **Workspace (outside git, `~/kepler-llvm-eval`, about 20 GB):** `llvm/LLVM-23.1.3-Linux-X64/bin`; Clang libraries `clang-ggml-cuda` (ffast), `-nofinite`, `-nofast`, `-ieee` (each with `libggml-cuda.so.0.9.11` and objects);
  `hybrid-nofinite`, `hybrid-nofast` (linked hybrids, with `collision-check.json`); `lib-*` directories (symlinks to the deployed libraries with one replaced; used as `LD_LIBRARY_PATH`);
  `kernel-cache` (cuobjdump results). Scripts in `llm-server research/kepler-clang/tools/`: `build_clang_ggml_cuda.py --math {ffast,nofinite,nofast,ieee}`, `link_hybrid.py` (collision check; `--use`, `--use-glob`),
  `run_card_hybrid.sh --execute NEW_DIR` (supervised; env options `HYBRID_CORR_LIBS`, `HYBRID_OPS`, `HYBRID_PERF`, `HYBRID_E2E`, `HYBRID_TEXT_LIBS`), `analyze_hybrid.py DIR`, plus the first-run tools.
- **Next:** (1) a short window testing the already built `ieee` library on attention and softmax (command in the report); (2) if it passes, bisect the relaxed settings one at a time (CPU-only builds); (3) a window with the server-based text check and the production 35B model before any deployment decision.
  Fix known: the first `llama-cli` text step hung for 50 minutes; it is replaced by a `llama-server` step (untested on the card).
- **How to run on the card:** only with the user allowing the exact command (the auto-mode classifier blocks stopping the production service otherwise). The supervised runners restart and health-check the service; check beforehand that nothing is connected
  (`ss -tn state established '( sport = :8080 )'`) and that the slot is idle. A faulty kernel could hang the card (no root here to reset it). Use only the card named in `~/.config/systemd/user/llama-server-one.service`, never `0000:04:00.0`.
  Restore by hand if needed: `systemctl --user start llama-server-one.service`, then `curl http://127.0.0.1:8080/health`.

### B. Driver (`haiku-k40c`): continue cardless S1 work
- **Read first:** its `AGENTS.md` (session protocol; **never read `tools/check_repo.py`**), `docs/STATUS.md`, `docs/S1-PLAN.md`, `docs/ABC-CARDLESS-OUTCOME.md`,
  `escalations/ESC-001.md`.
- **State:** host-side implementation passes (devinit interpreter, memory contract, native backend and bootstrap, A3 inventory); native link and load now
  pass on a KVM guest. `docs/STATUS.md` still says "native validation blocked (ESC-001)"; update it, citing the resolution in `ESC-001.md` and the evidence directory
  above. Unpushed commit `231b053`.
- **Open:** B2 real GPU mapping and publication, C2 and C3 full MMU/FIFO/channel integration, A5 decisions (GPIO, thermal, I2C device `0x20`; default deny),
  A7 and B5 and any card stage need the user. How to run a cardless native test: `python3 tools/haiku/cardless_run.py --base <opencode-haiku>/vm/system.qcow2 --cpus 2 --kvm
  [--driver build/haiku/k40_cardless_probe]` with `HAIKU_CROSS=$HOME/haiku-cross` (the VM must be shut down first; it uses a disposable overlay).

### C. Guest LLM (`haiku-k40c-llm`): validate the adopted profile
- **Read first:** its `AGENTS.md`, `docs/STATUS.md` (section "CPU profile adopted"), `docs/REPRODUCE.md`, `docs/NATIVE-RUN.md`.
- **Pending:** rerun this repository's native checks (build, sampler cases, FP32 matrix cases, Stories15M exact text match, server health) with the Ivy Bridge profile.
  Its VM tooling (`tools/app_vm.py`) is TCG with `-cpu qemu64`, which has no AVX, so it builds the baseline; the guest disk is not on this machine. Options: add a `--kvm`
  option like `opencode-haiku/tools/app_vm.py`, or run the build in the OpenCode repo's KVM VM. Evidence already exists there for the same pinned source: Stories15M text identical
  on baseline, Ivy Bridge and OpenMP builds. **Do not capture the Qwen3.6 graph** unless asked. Unpushed commit `e0e38fa`.

### D. Host server (`llm-server`): no action
Optional only with explicit approval: test OpenMP against llama.cpp's thread pool for the CPU experts in an idle window; confirm the running binary matches the intended build.

### E. OpenCode port housekeeping and cloud runs (OpenCode repo)
- **Pending:** a native Haiku rerun of scripts changed by `7970e38` (`services.sh`, `prodrun.sh`, `cloud-coding-task.mjs`, stricter cloud acceptance); more cloud models and repeats
  for variance with a new **no-credit** key (use `docs/SECRETS.md`: key file outside the repository, `tools/secrets/with-cloud-key.sh`, `serve-key-once.py` for the VM;
  the earlier key must be revoked); TUI session reconnect from a second concurrent client; multiple vCPU scaling (the VM has 2 vCPU).
- **The forum post and upstream offers (Haiku `get_executable_path()` for ggml, portability hunks) are deferred by the user.**

## 4. How to operate the Haiku VM (OpenCode repo, `vm/`; documented in `docs/KVM-VM.md`)
1. `sh vm/start-transfer.sh` in the background (localhost file service on `127.0.0.1:18080`), then `python3 tools/app_vm.py start --installed --kvm`; wait about 80 s.
2. Wake the screen (`key shift`); open a Terminal: click `1948,19` (Deskbar), click `1696,333` (Applications), `type 'Terminal'`, `key ret`. Click coordinates are in the
   2048-pixel frame (displayed coordinates times 1.06); take a fresh `screen` first.
3. In the guest Terminal: `curl -fsS http://10.0.2.2:18080/agent.sh -o /tmp/agent.sh; sh /tmp/agent.sh N &` with **N one above the last used job number** (last used: 710 in `logs/`; use 801 or higher).
   The agent runs `jobN.sh` strictly in order and never skips a number. Then `tools/job.sh N 'commands' [timeout_s]` from the host.
4. Shut down from inside Haiku (Deskbar leaf, Shutdown, Shut down buttons at `1948,19`, `1664,181`, `1208,546`); check `qemu-img check vm/system.qcow2`. Stop the transfer service.
5. Pitfalls: a black screen is the screen blanker; a crashed guest program opens a Haiku crash dialog that blocks everything until dismissed (choose Save report, then "Oh no!");
   never use `pkill -f` or `pgrep -f` with a pattern in your own command line; the Linux host has no `node` on `PATH` (use the bundled one as `NODE=...`), and `NODE` is needed for
   `python3 tools/test_t7610_runners.py` and `tools/test_review_runners.py`; guest copies of repository scripts under `/boot/home/opencode-haiku-src` date from 18 October.
6. Default Haiku llama.cpp profile: `ivybridge` (`tools/kvm-run/build-cpu-profile.sh`); runtime CPU variants work only with `GGML_BACKEND_DIR` set (ggml has no Haiku executable-path lookup);
   OpenMP costs about 40% decode speed on 2 vCPU; the HaikuPorts recipe flags build code that needs FMA and crashes on Ivy Bridge (`docs/COMMUNITY-COMPARISON-20261018.md`).

## 5. Index of this session's documents (OpenCode repo, `docs/`)
`STATUS.md`; `KVM-VM.md`; `T7610-KVM-HAIKU5-RESULTS-20261016.md`; `PHASE-1-3-RESULTS-20261018.md`; `FREE-MODELS-AND-CLOUD-TASK.md`; `SECRETS.md`; `AUDIT-2026-10-18-DISPOSITION.md`;
`HOST-CAPABILITIES-20261018.md`; `KEPLER-LLVM-STATIC-20261018.md`; `KEPLER-CARD-COMPARISON-20261019.md`; `KEPLER-HYBRID-20261020.md`; `COMMUNITY-COMPARISON-20261018.md`; `RUNNER-FIXES-20261019.md` (outside).
Results live under `results/t7610-2026101*/`. Build caches, source archives, models and virtual disks stay outside Git (`cache/`, `source/`, `vm/`, `share/`, `logs/`, `~/kepler-llvm-eval`).

## Addendum: hybrid work completed (20 October, evening)

Task A is closed: IEEE build, greedy text and 35B one-card benchmark are done (see KEPLER-HYBRID-20261020.md, "Final window"). Result: Clang attention failure is a code-generation difference; hybrid gain on 35B is within noise; decision is to keep nvcc. Optional later: diagnose the Clang attention failure.

## Addendum: workspace removed (21 October)

`~/kepler-llvm-eval` no longer exists; the paths above under it are gone. Rebuild steps: KEPLER-HYBRID-20261020.md, "Workspace removed".

## Addendum: Task E partly done (21 October)

Native Haiku rerun of `services.sh`/`prodrun.sh` passes; cloud task passes with 9 of the 10 free models under the
stricter acceptance (`jev-1.13-free`: no route). See TASK-E-20261021.md. Next guest job number: 835.
Remaining: second-client TUI reconnect, vCPU scaling, repeats, a native run of the `coding-workflow.mjs`
per-run upload names (fixed and host-tested on 21 October).

## Addendum: OpenCode work closed until the card is available (21 October)

Interactive TUI and browser use with a free cloud model, and a second concurrent client, pass
(INTERACTIVE-CLOUD-20261021.md). Guest `opencode-env.sh` now names haiku.5. The user considers the OpenCode part
done until the K40c is available. Optional leftovers: vCPU scaling, repeats, Jev retry, a native run of the upload fix.
Next guest job number: 845.
