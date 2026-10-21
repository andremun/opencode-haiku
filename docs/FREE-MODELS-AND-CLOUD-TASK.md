# Free cloud models and a real cloud coding task

18 October 2026 (Australia/Melbourne). The first part (measurements, documentation) used no
credentials. Later runs used one Console API key supplied by the user in chat for this test
(`OPENCODE_API_KEY`, passed to the client process only, redacted from saved logs, never written
to the repository; the user deletes it afterwards). No account was created, no credential store
read, and no client headers were spoofed.

## Measured today

| Check | Result |
|---|---|
| `GET https://opencode.ai/zen/v1/models` (anonymous) | HTTP 200, 85 models; ten ids end in or are named `-free`/`big-pickle` (`big-pickle`, `beam-free`, `mimo-v2.6-flash-free`, `nemotron-3.5-super-vl-free`, `nemotron-3.5-lightning-free`, `jev-1.13-free`, `longcat-2.5-preview-free`, `deepseek-v4.1-flash-free`, `glm-5.3-flash-free`, `space-bunny-free`) |
| Anonymous `POST .../chat/completions` for `glm-5.3-flash-free` with a one-word synthetic prompt, plain `curl` | **HTTP 403** `FreeTierError`: "free tier can only be used from within OpenCode" |

This reproduces the earlier rejections of 14 October (port binary and unmodified official
v1.19.0 anonymous) and is therefore not a port defect.

## From OpenCode's public documentation (secondary; read 18 October)

- The Zen page lists 14 free models "for a limited time" and describes signing in to the
  Console, adding billing and credits, and obtaining an API key. Anonymous use is not described.
- Data terms differ by model: zero retention and no training for GLM-5.3-Flash Free, DeepSeek
  V4.1 Flash Free, Space Bunny Free and LongCat 2.5 Preview Free; data may be used to improve
  the model for Big Pickle, Exo Free and the MiMo free models; the Nemotron free models are
  trial-only (no personal or confidential data). **Only synthetic code should be sent.**
- Whether a free model works with a signed-in account that has no billing is not stated.

## Not verified (from a third-party audit)

The audit report names header and tool-name "gates" (user agent >= 1.18.0, `x-opencode-client: cli`,
session id shape, `stream: true`, lowercase tool names) and a ban on deny-all permission fixtures.
These come from outside write-ups and issue threads; none was tested here. The earlier port
probes used deny-all permissions, so that combination is untested rather than disproved.

## How the key was supplied

A Console API key supplied by the user, never stored in the repository:

1. The key is set as `OPENCODE_API_KEY` in the environment of the single command that runs the task,
   with `OPENCODE_CLOUD_PASS_API_KEY=1` as an explicit opt-in. The runner passes it to the client
   process only and redacts it from the saved logs and outcome.
2. For the VM run, the key was carried in a one-off job script that was deleted afterwards (the
   guest's temporary copy was overwritten by the next job). The repository, results, commit and guest
   were scanned for the key and the user revokes it.
3. An alternative that keeps the key out of the agent's hands entirely: the user logs in with
   `opencode auth login` using a private `XDG_DATA_HOME` and the runner reads
   `OPENCODE_CLOUD_DATA_HOME` (not used in this run).

For future sessions use the key file, wrapper and one-shot server in [SECRETS.md](SECRETS.md).

Use the official release or the Haiku.5 port (`2.0.29-haiku.5`, above the 1.18.0 minimum).

## The task

`examples/cloud-task/` is a synthetic, multi-file Node project (no dependencies): `src/csv.mjs`
(`parseCSV`: quoted fields, escaped quotes, embedded newlines, CRLF, errors) and `src/report.mjs`
(`summarize`: group, sum, round, sort, errors), with 15 tests under `test/`. The starting project
passes 3 and fails 12; a reference solution passes 15/15.

Runner: `tools/tui-port/cloud-coding-task.mjs OUTPUT_DIR` with `OPENCODE_TEST_PORT_ROOT`
(launcher), `OPENCODE_CLOUD_MODEL` (for example `opencode/glm-5.3-flash-free`) and optional
`OPENCODE_CLOUD_PASS_API_KEY=1` with `OPENCODE_API_KEY`, `OPENCODE_CLOUD_DATA_HOME`,
`OPENCODE_TEST_STEPS` (default 20), `OPENCODE_TEST_TIMEOUT_MS` (default 20 min) and
`OPENCODE_CLOUD_OFFLINE=1` (host controls only: disables the model catalogue fetch).
Permissions: read anywhere, edit `src/*`, run `node --test*`, plus `tail *` and `head *` for piped
output. The runner puts its own Node first on the agent's PATH.
Acceptance: tests unchanged, the agent ran `node --test` successfully at least once, and an
independent `node --test` passes. The outcome JSON also records tool calls, timing and any
`FreeTierError`/`UpgradeRequired` text, so a rejected run is distinguishable from a wrong answer.

Host controls (no network, no model): solved, did-not-run-tests, tampered-tests and unsolved
launchers give pass, fail, fail, fail (`tools/test_t7610_runners.py`).

## Results with an authorised key (model `opencode/glm-5.3-flash-free`, synthetic task)

A raw `curl` with the key still got the free-tier 403 ("only from within OpenCode"); the key lists
models but only an OpenCode client could use the free tier. With a client, the model solved the task.

| Run | Client | Steps | Agent ran tests | Independent tests | Accepted | Time |
|---|---|---|---|---|---|---|
| official-first | official v2.0.29 (host) | 12 | 2 (both "node: command not found") | 14/15 | no (harness defect) | 420 s |
| official-rerun2 | official v2.0.29 | 12 | 0 (piped command denied) | 15/15 | no (harness defect) | 185 s |
| official-rerun3 | official v2.0.29 | 12 | 1 | 15/15 | yes | 62 s |
| haiku5-bundle-host-first | Haiku.5 bundle on Linux | 12 | 0 (piped command denied) | 15/15 | no (harness defect) | 127 s |
| haiku5-bundle-host-final | Haiku.5 bundle on Linux | 20 | 2 | 15/15 | yes | 237 s |
| official-final | official v2.0.29 | 20 | 3 | 15/15 | yes | 93 s |
| **haiku-vm-run** | **Haiku.5 port inside the KVM Haiku VM** | 20 | 2 | **15/15** | **yes** | 430 s |

Evidence: `results/t7610-20261018-cloud/` (outcome JSON and redacted agent logs; no key).

The harness defects were mine and are fixed in `cloud-coding-task.mjs`: the model catalogue fetch
was disabled (client reported "Model unavailable"); `node` was not on the agent's PATH; the
shell permission matched only the exact string `node --test`; and piped commands are checked part by
part, so `tail`/`head` needed allow rules. In the rerun3 and rerun2 logs the model reported honestly
that it could not run the tests rather than claiming success.

What this shows: the Haiku.5 port in the Haiku VM can drive a real free cloud model through a
multi-file edit-and-test loop (read, write, edit, shell) and the result passes an independent
test run. What it does not show: model quality in general (one task, one model, a few runs),
behaviour with paid models, other free models, the TUI/GUI paths, or anything about the K40c.
The free model's data terms were not relevant here because the project is synthetic.

## Status

Runner, task and controls validated; the run succeeded in the Haiku VM with the user-supplied key
(`results/t7610-20261018-cloud/haiku-vm-run.log`). Not covered: other models, paid models, repeated
runs for variance, TUI/GUI paths.

## 19 October 2026: stricter offline acceptance

The runner now also requires a clean client exit with no timeout and at least one
completed agent test with explicit exit 0 and a Node summary showing a positive
test count, all passed and zero failed. This handles both observed metadata shapes
and rejects a `tail` pipeline that hides failing tests. Correct edits and independent
test success after a client failure remain visible in the outcome, but do not pass
end-to-end acceptance. New offline controls cover failed/unknown shell status,
failed client exit, timeout and a hidden test failure. No new real-model run was
made; the earlier measured outcomes above are retained as originally recorded.

## 21 October 2026: more free models in the Haiku VM

Under the stricter acceptance, through the Haiku.5 port in the KVM Haiku VM, with a new no-credit key:
`glm-5.3-flash-free` (twice, 156 s and 113 s), `big-pickle`, `beam-free`, `mimo-v2.6-flash-free`,
`nemotron-3.5-super-vl-free`, `nemotron-3.5-lightning-free`, `longcat-2.5-preview-free`,
`deepseek-v4.1-flash-free` and `minimax-m3.1-flash-free` all pass (15/15). `jev-1.13-free` fails with
`provider.no-route` ("Model unavailable") before any model turn. The catalogue now lists
`minimax-m3.1-flash-free` and no `space-bunny-free`. One run per model except GLM.
Details: [TASK-E-20261021.md](TASK-E-20261021.md).
