# Status

Updated 15 October 2026 (Australia/Melbourne). Independent OpenCode Haiku port.

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

## Current result: packaged Haiku.5 terminal acceptance

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

## Manual T7610 work prepared, not measured

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

## Boundaries and resources

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

## Push/handoff blocker

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
