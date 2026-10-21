# Status

Updated 21 October 2026 (Australia/Melbourne). Independent OpenCode Haiku port.

## 21 October 2026: interactive use with a cloud model (OpenCode part done until the card is available)

With a free cloud model and the Haiku.5 port in the cardless VM: the CSV/report task passes interactively in
the TUI (15/15). A second TUI attached to the live session shows the history, and messages from either client
appear live in the other. The browser (WebPositive) opens the same session and makes a verified edit, which
appears in the TUI. Found: the TUI ignored the project's `model` and started on a subscription model (Claude Haiku 5.5,
OpenCode Go), and the picker mixes free and subscription models. Check the footer before prompting. The guest
env file now names haiku.5. [INTERACTIVE-CLOUD-20261021.md](INTERACTIVE-CLOUD-20261021.md).

## 21 October 2026: Kepler LLVM workspace removed

The user deleted `~/kepler-llvm-eval` (15 GB: LLVM 23.1.3, Clang and hybrid libraries). Nothing used it; the service runs the
nvcc library and was healthy before and after. Text results kept in `results/kepler-llvm-eval-summary/`. Rebuild steps:
[KEPLER-HYBRID-20261020.md](KEPLER-HYBRID-20261020.md), "Workspace removed".

## 21 October 2026: Task E, native runner rerun and more free cloud models

The runners changed by `7970e38` pass natively on Haiku (cardless KVM VM, source `b66fa4f`):
`prodrun.sh ivybridge` exits 0 (8-step coding fixture `semantic_pass`, stack cleaned up). In `services.sh`
scoped mode a duplicate listener is refused and a failing check exit (7) propagates with both servers
stopped. With a user-created no-credit key (served once to the guest, never stored), the cloud
task passes the stricter acceptance with 9 of the 10 listed free models (15/15 each; GLM twice); `jev-1.13-free`
fails with client `provider.no-route` before any model turn. Found: `coding-workflow.mjs` uploads to
fixed `results/` names and overwrote three tracked files (restored); it now uses per-run names
(host control added, not yet rerun on Haiku). Still pending: second-client TUI reconnect,
more than 2 vCPUs, repeats for variance. [TASK-E-20261021.md](TASK-E-20261021.md).

## 20 October 2026 (final window): IEEE, greedy text, 35B production model

Pure Clang attention still fails with strict IEEE (2411/2832): a code-generation difference, not a math flag; cause not found. Hybrid libraries pass all
correctness tests and give identical greedy text on 9B; on the 35B production configuration (one card) generation is 13.34 (nvcc), 14.07 (hybrid), 12.60
(nvcc repeat) tokens/s: within noise. Text is not bit-identical (diverges after ~90 characters on one prompt). Decision: keep nvcc, do not deploy. First-window
text/35B data were invalid (server not stopped; fixed). Service paused twice, restored healthy both times. [KEPLER-HYBRID-20261020.md](KEPLER-HYBRID-20261020.md).

## 20 October 2026 (later): Clang fixes and hybrid libraries on the card

A hybrid `libggml-cuda` (24 files from Clang: quantised matrix kernels and softmax; attention and the rest from nvcc) passes all tested
operations and speeds up token generation by about 5% on Qwen3.5-9B; the full Clang build still fails attention (NaN; `-fno-finite-math-only`
did not fix it). Service paused 12:21 to 14:04, restored and healthy; 50 minutes were lost to a hung `llama-cli` step (fixed in the runner, untested).
Not deployed. [KEPLER-HYBRID-20261020.md](KEPLER-HYBRID-20261020.md).

## 20 October 2026: card comparison, driver and guest-LLM follow-ups

- The on-card comparison ran (service paused 08:56 to 10:40, restored and healthy): Clang-built `libggml-cuda` passes
  all tested operations except flash attention (NaN in 417 of 2,832 cases, probably `-ffast-math` assuming finite
  values); production quantisation kernels about 5 to 15% faster at the median; i-quant kernels about 5x slower.
  [KEPLER-CARD-COMPARISON-20261019.md](KEPLER-CARD-COMPARISON-20261019.md). The run used the runner as of `784ef26`.
- Driver repository: ESC-001 resolution committed there (`231b053`, not pushed). Guest-LLM repository: Ivy Bridge
  profile adopted with a baseline fallback (`e0e38fa`, not pushed). Context for separate sessions:
  [SESSION-HANDOFF-20261020.md](SESSION-HANDOFF-20261020.md).

## 19 October 2026: offline review fixes

Fixed cloud acceptance to reject a failed/timed-out client, failed or unknown-status
agent tests, and a pipeline hiding test failures. The CPU production runner now
uses scoped service ownership; startup refusal cannot lead to tests against or
cleanup of a pre-existing stack. The prepared GPU runner now fails on correctness
errors and uses one bounded Linux subreaper supervisor, which drains test descendants
before attempting service restoration. The independent restart timer was removed.
GPU execution remains pending and requires separate authorisation; SIGKILL of the
supervisor, a stuck kernel task, or host failure requires manual recovery.

Offline controls pass: 18 existing host tests plus 7 new regression groups.
No new VM, cloud-model, GPU or production-service run took place. Existing CPU/KVM
and cloud results remain historical evidence; the stricter cloud acceptance has
not been re-run with a real model. No push was attempted. Details, commands, limits
and source hashes: [RUNNER-FIXES-20261019.md](RUNNER-FIXES-20261019.md).

The dated sections below record prior runs. The 15 October snapshots at the bottom
retain their original pending work and resource state for provenance; they are not
current operational state or permission to push. The latest saved KVM run records
clean shutdown; this fix pass did not inspect or change its present state.

## 16 October 2026: Haiku.5 on the persistent KVM VM (T7610)

Haiku.5 was rebuilt on this host (archive `9cbd07c5...`, not byte-identical to the
recorded `b9970cd8...`: different SDK/Koffi/renderer inputs) and run in the cardless
KVM VM. Pass: install and self-test, 54 native daemon tests with fmt/Clippy,
API probes, baseline and Ivy Bridge llama.cpp builds, direct inference, 8-step
coding fixture (`semantic_pass` true), TUI terminal pane, child exit, clipboard
paste and cleanup. Ivy Bridge build is much faster than baseline in the 3-repetition
synthetic benchmark (prompt 11.0 vs 0.83 tok/s at 512/128). Not tested here:
WebPositive terminal panel, TUI resize/reconnect visuals, TUI latency per profile.
Details, hashes and limits: [T7610-KVM-HAIKU5-RESULTS-20261016.md](T7610-KVM-HAIKU5-RESULTS-20261016.md).

### 17 October 2026 addendum: production-matching CPU build

A guest build matching the host llm-server CPU configuration (`GGML_NATIVE=ON`,
OpenMP) passes the same builds, benchmark, inference and coding fixture. Without
OpenMP it passes too and decodes about 40% faster in this 2-vCPU guest. See the
addendum in [T7610-KVM-HAIKU5-RESULTS-20261016.md](T7610-KVM-HAIKU5-RESULTS-20261016.md).

### 19 October 2026: community comparison and Kepler static study

Compared with the community llama.cpp work on Haiku: our patch is a superset for b8861; the HaikuPorts recipe flags
(`GGML_NATIVE=OFF`) enable AVX2/FMA/BMI2 and the resulting build crashes on this Ivy Bridge CPU; runtime CPU variants
work on Haiku once `GGML_BACKEND_DIR` is set (ggml has no Haiku executable-path lookup), reaching near the tuned
build; OpenMP again cost about 40% decode speed; mimalloc did nothing:
[COMMUNITY-COMPARISON-20261018.md](COMMUNITY-COMPARISON-20261018.md). Host capabilities and a GPU-free comparison of
Clang 23 with nvcc 11.4 for Kepler kernels: [HOST-CAPABILITIES-20261018.md](HOST-CAPABILITIES-20261018.md),
[KEPLER-LLVM-STATIC-20261018.md](KEPLER-LLVM-STATIC-20261018.md).

### 18 October 2026: phases 1 to 3 of the continuation plan

The driver's native link/load gate (ESC-001) is unblocked and passes on the KVM guest (probes link
against the byte-identical guest kernel; cardless load prints `k40_os: PASS`). Ivy Bridge, OpenMP
off, is now the default Haiku llama.cpp profile (same Stories15M text as Linux; OpenCode exchange
40 s against 165 s on the baseline). Browser terminal panel, TUI resize and reconnect pass on the
KVM build; the renderer hash difference is only an embedded cache path. Details:
[PHASE-1-3-RESULTS-20261018.md](PHASE-1-3-RESULTS-20261018.md).

### 18 October 2026: audit disposition and cloud task

An external static audit was checked: eight findings were valid and fixed (transfer-server dot
names, split ghostty pin, probe spawn errors, runner log upload, stale default, personal path,
diagnostic guard, missing-archive error), four were not changed, two were incorrect. See
[AUDIT-2026-10-18-DISPOSITION.md](AUDIT-2026-10-18-DISPOSITION.md). Free cloud models still reject
anonymous requests (403 FreeTierError). With a user-supplied key, a real multi-file coding task
passes with the free `glm-5.3-flash-free` model through the Haiku.5 port inside the Haiku VM (15/15
tests, 430 s) and through the official client; the key was never stored in the repository:
[FREE-MODELS-AND-CLOUD-TASK.md](FREE-MODELS-AND-CLOUD-TASK.md). Key handling for future runs (out-of-repo key file, wrapper, one-shot
server for the VM, secret scan, free-model guard): [SECRETS.md](SECRETS.md).

## 15 October historical snapshot: packaged Haiku.5 terminal acceptance

**The packaged TUI terminal crash is fixed.** Standard builds now apply the
Haiku Ghostty VT renderer patch and produce 2.0.29-haiku.5. Fresh installation,
native self-test, file/shell/session controls and both terminal APIs pass.

Visual checks in the local cardless TCG Haiku VM pass: TUI shell I/O and UTF-8,
window resize, session reconnect, new input after replay, child exit without
crash, native clipboard paste; WebPositive shell I/O and UTF-8, window resize,
full page reload/restoration, subsequent input and child exit. Terminal metadata
was cleaned through the APIs. See [HAIKU5-ACCEPTANCE.md](HAIKU5-ACCEPTANCE.md)
for exact coverage, intermediate observations and limitations.

Full output from 54 native daemon tests, formatting and Clippy is captured with
exit 0 in results/haiku5-native-terminal-suite.log. Nine host regression groups
pass, including hidden failure controls, immutable coding tests, launcher errors,
atomic result publication and host-platform guards. Build/installation and API
logs, screenshots, native hashes and selected input provenance are in results/.

This run uses Haiku hrev60207, Node 24.21.0-1, 2 qemu64 TCG vCPUs and 8 GiB.
No new real-model inference ran in this continuation; native CPU model and
shared-session GUI/TUI inference remain established by the earlier acceptance.
The current archive is 53,682,981 bytes, SHA-256
b9970cd8592ad48050c9340579c6d3e4d3d7c326e7e603cb921afbea481cf8f2.
The runtime manifest includes both terminal backend hashes and the actual SDK/
addon variants used. Models, archives, source/dependency caches, SDKs and disks
remain outside Git.

## 15 October historical snapshot: manual T7610 work prepared

The user confirmed that the T7610 can only be accessed manually. Its next step
is to pull the committed code and follow [T7610-NEXT-RUN.md](T7610-NEXT-RUN.md).
Added tooling stages committed source and a checksum-verified runtime for the
guest without SSH. It builds separate baseline and guarded Ivy Bridge AVX/F16C
profiles and benchmarks batches 128/32 versus 512/128. AVX2/FMA/BMI2 remain off.
No performance or numerical result for those new builds is claimed yet.

The revised coding fixture uses eight steps by default, fresh state each run,
an unchanged immutable test, an actual agent shell test and an independent
verification. Correct edits without the agent's test are recorded separately.
A new real-model run is pending on the T7610; resource/time limits remain distinct
from coding-quality failures. Source inspection confirms the custom agent system
prompt already replaces the default. No workspace/permission instructions were
removed as a speculative speed patch.

The reviewed T7610 commit 0344fbb has its own evidence: native CPU controls,
GUI/TUI session sharing, both terminal APIs and a correct model-made edit. Its
claimed 54-test run needs a complete reliable capture; the saved tail showed only
nine service tests and the old shell pipeline masked status. The new TCG log
cannot replace that missing T7610 evidence. See T7610-COMMIT-REVIEW.md and
T7610-KVM-RESULTS-20261015.md. The old roughly threefold direct wall-time ratio
is not an isolated KVM speed measurement because hardware/cache states differ.

## Sources and installation

OpenCode 34d8ded0c58dd66808c1d60e081e8c66da12a896; OpenTUI 0.5.17;
Bun 1.4.2 (Linux build), patched Zig 0.16.0 and Koffi 3.3.3. Native daemon 0.2.0
is pinned at 878aa26ab1916f8d41a0ccb90d55a372d01abf69; Ghostty parser at
ab0b9da9e88fcb4b0533a1854e84628f663930af. Reference manifests retain original
and T7610 rebuilt artifact provenance. Complete installation, llama.cpp patches,
model download and mixed-platform rebuilding: T7610-HAIKU-SETUP.md / INSTALL.md.

## 15 October historical snapshot: boundaries and resources

No host sudo, physical GPU, host driver or existing host LLM-service change.
This is CPU/cardless evidence and establishes no K40c compute support. The driver
repository was inspected read-only to answer a feasibility question; no driver
work was started. Recursive watching, clipboard images/primary selection and
native Electron remain unsupported. Browser tab styling, slow initial rendering
under emulation, one fast synthetic keystroke omission and empty-stream clipboard
write are recorded limitations. Reliable autonomous coding is not established.

The private Haiku.5 backend and both TUI test clients stopped after PID/command
verification; the browser was closed, its terminal records removed, and the guest
clipboard restored. The owned guest job agent and host localhost transfer service were stopped. The cardless VM is
left running for inspection. Push is explicitly requested; it is not yet confirmed.

## 15 October historical snapshot: push/handoff blocker

Implementation and evidence were committed as `27ebd52`. The staged source
archive and generated deployment script were validated from that committed HEAD.
The requested `git push origin main` was attempted on 15 October 2026, but
**automatic approval review rejected it before Git executed**. The stated reason
was that the trusted conversation did not explicitly authorise this payload's
export to the specific GitHub destination and did not establish destination trust.
No alternate transport or indirect push was attempted.

To retry, the user must explicitly confirm pushing this repository's committed
code, patches, documentation and synthetic test evidence to
`https://github.com/andremun/opencode-haiku.git`, branch `main`. Models, runtime
archives, source/dependency caches, SDKs and VM disks are excluded from Git.
An earlier HTTPS remote check also lacked GitHub credentials; that may require
local authentication after the approval block is resolved. Nothing was pushed
by this continuation. T7610 manual measurements remain pending.
