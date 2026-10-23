# Offline runner fixes — 19 October 2026

Based on reviewed OpenCode port commit `784ef26`. This pass implements fixes for the four review findings using CPU-only controls. No VM was started, no real model or credential was used, and no GPU, running service or host driver was accessed. No push was attempted.

## Changes

- Cloud acceptance requires a clean client exit, no timeout/launch error, unchanged tests, a successful agent test and the independent test pass. Agent test success needs explicit shell exit 0 plus the Node summary (positive test count, all passed, zero failed). Supports the two metadata shapes observed in saved logs. A pipeline whose shell exit hides Node test failure no longer qualifies. Outcome fields retain failed-client status, independent success and the new successful-agent-test count separately. Timeout input is validated.
- `services.sh [COMMAND ...]` keeps process ownership and its cleanup trap until the command finishes. Existing no-command service startup remains available. `prodrun.sh` uses scoped mode, aborts after startup refusal, preserves failures and checks the coding outcome. It no longer reads persistent PID files for cleanup. `OPENCODE_GUEST_HOME` permits temporary, fake guest layouts in host tests; the default remains `/boot/home`.
- The prepared card comparison now requires explicit `--execute NEW_OUTPUT_DIR`. One Linux child-subreaper supervisor bounds the complete test window at 150 minutes. It stops and reaps owned descendants, including background children that create a session, before attempting restoration. It has no independent service-restart timer. Correctness, performance and benchmark failures propagate; a correctness failure prevents later performance/model runs. A pause marker ensures partial stop attempts also trigger restoration. The worker requires the target service to be initially active and validates its inputs before pausing. Failed start/health/deadline restoration returns failure. No on-card run occurred.
- Status now distinguishes the dated 15 October snapshots from newer results and from current push authorisation. Historical results and their original hashes are retained.

## Verification

All test writes were in a temporary tracked-source copy `/tmp/opencode-review-20261019`, not source caches or VM disks. Node was the bundled executable:

```
NODE=/home/unimelb.edu.au/mariom1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node
export NODE
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_t7610_runners.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_review_runners.py
sh -n tools/kvm-run/services.sh
sh -n tools/kvm-run/prodrun.sh
bash -n llm-server research/kepler-clang/tools/run_card_comparison.sh
```

The existing suite needs temporary localhost listeners. These commands ran with that restriction lifted; no real service endpoints were used. **18 existing host tests and 7 new regression groups pass.** Full logs and exact changed source hashes are in `results/20261019-runner-fixes/`. Python files also passed `ast.parse`; no compiled cache was written. ShellCheck is unavailable on this host.

New groups cover seven cloud outcome variants (both exit-metadata shapes, client failure, failed/unknown test status, timeout and hidden pipeline failure), startup refusal with a live sentinel PID in an old file, scoped cleanup of both fake services after check failure, explicit execution gating, worker/restoration/no-pause failures, process termination and reaping before restoration on timeout/SIGTERM/normal background exit, and the actual shell worker with all service/GPU commands replaced by stubs. The shell-worker controls cover first correctness failure, a complete fake A-B-A comparison and failed restoration health checks.

The initial unmodified review suite had environment failures inside the sandbox (Node absent on PATH, then blocked localhost sockets/child output). It passed after selecting bundled Node and permitting temporary localhost servers. Those were test-environment limitations rather than port defects; no failed control was suppressed. The new controls were developed and run outside that same restriction.

## Limits and next validation

The supervisor is Linux-only preparation for the host comparison, not a Haiku GPU feature. If it is itself killed with SIGKILL, the host fails, or an owned task cannot be killed, automatic recovery is not guaranteed. It refuses restoration when owned test processes remain; manual recovery is then required. The design deliberately removes the unsafe promise that a restart timer can always restore production regardless of live test processes.

Mocked process ordering does not prove recovery from a real GPU hang. Real card execution, stopping/restoring a production service, cloud reruns under the stricter gate, and a native Haiku rerun of the changed CPU scripts remain untested. Earlier saved KVM/CPU/cloud successes remain their original evidence, not results of this revision. No new runtime binary, kernel, source/patch pin or model was built or changed.
