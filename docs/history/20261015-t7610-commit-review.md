# Review of the T7610 commit

15 October 2026 (Australia/Melbourne). Reviewed commit:
`0344fbb76a5049e06322f46c0e1740386d464466`.

The commit adds useful native evidence: successful model-driven editing,
file/shell/session controls, legacy browser PTY API and persistent daemon API
checks. Its screenshots show both the stock renderer crash and an experimental
renderer executing commands with UTF-8 output. The implementation remains
experimental: the packaged renderer still cannot open the TUI terminal pane.

## Findings and revisions

1. **P1 — verification scripts hide test failures.** Original
   `tools/kvm-run/pty.sh:4-6` and `native.sh:24` pipe Cargo into tail, which returns
   success even when Cargo fails. `api.sh:11` prints the upload command's status
   instead of the preceding Node test's status; earlier probes also continue
   after failure. Corrected: full test/Clippy logs, immediate native failure,
   explicit per-probe status and aggregate API failure. llama/model/coding
   runners now propagate failures too. Existing raw logs were not rewritten.

2. **P2 — host job success does not mean guest success.** Original
   `tools/job.sh:4` returns cat's status and accepts an incomplete output file;
   the transfer server writes the published result in place. Corrected:
   validate the guest's final exit marker, return its code, atomically publish
   requests/results, reject reused job numbers, and retry uploads without
   rerunning a completed command. A wait deadline does not cancel execution;
   the tool says so explicitly and returns 124.

3. **P2 — sequence labelled cold was warmed by smoke inference.** Original
   `tools/kvm-run/inf.sh:13-15` submits an inference before cold1. The saved
   first cold1 response has cache_n=5; first cold2 has cache_n=0. Within each
   sequence, later requests reuse three prefix tokens. Corrected: no pre-test
   smoke inference, fail on readiness deadline/process exit, refuse an existing
   listener, stop only the model child started by the benchmark. HTTP failures
   and malformed completion responses make inference-compare.cjs fail.
   Existing timings are retained with corrected labels. A threefold reduction
   in total wall time is not an isolated measurement of KVM acceleration.

4. **P2 — service startup overwrites credentials and can start duplicates.**
   Original `tools/kvm-run/services.sh:3-8` replaces a chosen password with a
   literal placeholder every run. It also starts processes without establishing
   exclusive ownership/readiness. Corrected: preserve existing configuration,
   generate a private credential only when absent, reject the old placeholder,
   refuse existing listeners, wait for owned processes and clean up new
   children on failed startup. Existing host services were not accessed.

## Evidence qualifications

The T7610 retry capture proves nine service tests passed; it does not retain
all 54 results or a reliable Cargo status. The earlier development platform has
its own complete 54-test evidence, which cannot substitute for a full T7610
rerun against a different parser binary. The T7610 persistent-terminal API log
independently shows its expected PASS events and child exit 5.

The model changed subtraction to addition, but did not call the shell test.
The recorded manual test success and incomplete agent workflow are separate.
Resource limits are not treated as coding-quality acceptance failures.

The Ghostty VT patch worked in the recorded manual test, but remains outside
the default build and runtime archive. It must be integrated, rebuilt and
accepted through TUI/browser tests before claiming the packaged terminal works.
The browser terminal panel itself was not visually tested.

## Validation of this revision

`python3 tools/test_t7610_runners.py` exercises host-only controls with fake
Cargo/API executables and an isolated HTTP server: failing Cargo tests/Clippy,
failing API with a successful upload, guest exit propagation, missing status,
reused jobs, wait timeout, atomic result replacement, duplicate service refusal,
and HTTP/malformed completion failures. These checks use no VM or real model.
Shell/Node/Python syntax and Git whitespace checks also run.

A fresh native T7610 run is still needed for full-suite logs, corrected cold
sequences and revised service/agent operation. This review neither regenerates
the runtime archive nor changes the experimental renderer's acceptance status.
No host sudo, GPU access, push or existing model-service change was performed.
