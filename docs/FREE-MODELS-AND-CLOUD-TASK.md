# Free cloud models and a real cloud coding task

18 October 2026 (Australia/Melbourne). Nothing here was run with credentials. No account
was created, no login performed, no existing credential store read, and no client
headers were spoofed.

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

## What is needed to run the task

A signed-in session of an OpenCode client, supplied by the user. Suggested split that keeps
credentials out of the agent's hands and out of Git:

1. The user runs `opencode auth login` for the `opencode` provider (or the equivalent official
   flow) with `XDG_DATA_HOME` set to a private directory, for example `~/opencode-cloud-auth`.
2. The agent runs the task with `OPENCODE_CLOUD_DATA_HOME` pointing at that directory; the runner
   passes it through and never reads or prints it. Use the official release or the Haiku.5 port
   (`2.0.29-haiku.5`, version above 1.18.0).

## The task

`examples/cloud-task/` is a synthetic, multi-file Node project (no dependencies): `src/csv.mjs`
(`parseCSV`: quoted fields, escaped quotes, embedded newlines, CRLF, errors) and `src/report.mjs`
(`summarize`: group, sum, round, sort, errors), with 15 tests under `test/`. The starting project
passes 3 and fails 12; a reference solution passes 15/15.

Runner: `tools/tui-port/cloud-coding-task.mjs OUTPUT_DIR` with `OPENCODE_TEST_PORT_ROOT`
(launcher), `OPENCODE_CLOUD_MODEL` (for example `opencode/glm-5.3-flash-free`) and optional
`OPENCODE_CLOUD_DATA_HOME`, `OPENCODE_TEST_STEPS` (default 12), `OPENCODE_TEST_TIMEOUT_MS`
(default 20 min). Permissions: read anywhere, edit `src/*`, run `node --test` only.
Acceptance: tests unchanged, the agent ran `node --test` successfully at least once, and an
independent `node --test` passes. The outcome JSON also records tool calls, timing and any
`FreeTierError`/`UpgradeRequired` text, so a rejected run is distinguishable from a wrong answer.

Host controls (no network, no model): solved, did-not-run-tests, tampered-tests and unsolved
launchers give pass, fail, fail, fail (`tools/test_t7610_runners.py`).

## Status

Task, runner and controls ready; **no cloud model has run the task** because no authorised session
exists. Results from a free model would say nothing about the Haiku VM's local model or the K40c.
