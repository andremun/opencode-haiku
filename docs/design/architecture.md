# OpenCode headless Haiku port

Recorded 14 October 2026. This is a native Haiku Node CLI prototype, with a
separate CPU model server used for local inference tests. It is not evidence
of K40c compute support. Interactive OpenTUI and native PTY terminals are not
ported.

## Source and build

OpenCode source: `34d8ded0c58dd66808c1d60e081e8c66da12a896`, package version
2.0.29. Archive, lockfile, Bun and patch SHA-256 values are in
`reference/opencode-port-manifest.json`. The archive's default build version
was `0.0.0-main-202610141022`; the reproducible port build uses the upstream
`OPENCODE_VERSION=2.0.29-haiku.1` and `OPENCODE_CHANNEL=haiku` settings.

Build tools: Bun 1.4.2; upstream Node bundle verifier 26.4.0. Haiku runtime:
nodejs24 24.21.0-1 on Haiku hrev60207 x86_64. Frozen installation used
`bun install --frozen-lockfile --ignore-scripts`. Lifecycle scripts were not run.

The two-file patch defers loading `@lydell/node-pty` until an interactive PTY
is requested, and advertises the persistent PTY helper only on Linux/macOS,
where binaries exist. It preserves the real unsupported-operation failure
rather than inventing a terminal implementation.

Rebuild from this repository:

```sh
sh tools/opencode-port/build.sh   # removed on 2026-10-23; see Git history
```

This fetches pinned inputs if missing, checks their hashes, applies the patch,
installs the locked dependencies, runs upstream `build-node.ts --bundle-only`,
and packages the bundle, assets, launcher and upstream MIT license. Generated
sources, dependencies and archives remain ignored by Git. Network access is
needed; no sudo is used. The script is assembled from the executed build steps;
an additional clean rebuild with this wrapper has not yet been run.

The generated archive is
`share/opencode-haiku-headless-2.0.29-haiku.1.tar.gz`; its hash is recorded in
`results/20261014-headless-port/opencode-package.json`. Extract it in a directory on Haiku after
`pkgman install nodejs24`. Run `./opencode --help` and use `run --standalone`
for a private server. Invoking the launcher without arguments displays help.
The package retains Linux native assets from the upstream build: those assets
cannot implement Haiku PTY, native search or watching. Help and tested APIs do
not require loading the PTY asset.

## Measured results

| Check | Outcome | Evidence |
|---|---|---|
| Native Node filesystem, subprocess, SQLite WAL/BigInts, module hooks, HTTPS | Pass | `results/20261014-headless-port/opencode-guest-runtime.log` |
| Unpatched CLI launch | Failed: Linux native PTY module | `results/20261014-headless-port/opencode-guest-baseline.log` |
| Patched native help/version | Pass | `results/20261014-headless-port/opencode-guest-port.log` |
| Core typecheck | Pass | `logs/opencode-core-typecheck.log` |
| Root lint | Pass, existing warnings | `logs/opencode-check.log` |
| Full typecheck under Turbo's strict environment | Failed: Astro attempts to write outside workspace | `logs/opencode-check*.log` |
| Full typecheck with isolated XDG config and `--env-mode=loose` | 36/36 tasks pass | `logs/opencode-typecheck-loose.log` |
| Actual native file write/read API | Pass | `results/20261014-headless-port/opencode-guest-api-probe.log` |
| Actual native shell runs Node assertions | Pass, exit 0 and `API_SHELL_PASS` | Same |
| Stored session recovered after private server restart | Pass | Same |
| Free provider from Haiku | Failed, HTTP 403 | `results/20261014-headless-port/history/opencode-guest-free-model-attempt2.log` |
| Free provider from official Linux v1.19.0 | Same HTTP 403 | `results/20261014-headless-port/opencode-official-free-model.log` |

The API probe uses the actual OpenCode server and services. It writes a small
addition function, reads it back, executes positive and negative argument
assertions through `/api/shell`, then creates a session and verifies its ID and
title after a server restart. This tests stored session metadata, not a resumed
LLM conversation or model-directed editing.

The full typecheck command that passed, from the extracted source root:

```sh
ASTRO_TELEMETRY_DISABLED=1 \
XDG_CONFIG_HOME="$PWD/../../cache/opencode-check-state/config" \
../../cache/build-tools/bun-1.4.2/bun-linux-x64/bun \
  turbo typecheck --env-mode=loose --concurrency=3
```

The ordinary root check reached the unrelated Astro packages, which lost the
XDG/telemetry environment through Turbo's default strict filtering. We retained
both failures and reran typechecking with that environment forwarded. No
unrelated source files were changed to make these checks pass.

## Model access

[OpenCode's current model documentation](https://opencode.ai/v2/docs/console/models/)
lists free models, including Big Pickle. The pinned provider source supplies
public credentials and disables models with positive input costs without a
real key. This does not guarantee anonymous access from this environment.

A direct anonymous request was rejected as restricted to OpenCode. The first
actual port request was rejected with HTTP 426 because the archive build used
the `0.0.0` development version. Correcting build metadata to the actual source
version resolved that version error, but the service then returned HTTP 403,
again saying free access is restricted to OpenCode. The unmodified, checksum-
verified official Linux v1.19.0 release returned the same restriction. We did
not spoof a different client or channel, change accounts, or use a paid model.
On 18 October an anonymous `curl` request to a free model returned the same 403, and the
public documentation describes signing in and using an API key; the detailed header/entitlement
rules reported elsewhere are unverified. See [FREE-MODELS-AND-CLOUD-TASK.md](../history/20261018-free-models-and-cloud-task.md).

A host probe was initially rejected by automatic approval review because it
could inherit an existing API key. The probe now forwards an explicit allow-list
of environment variables excluding credentials and uses isolated XDG state.
Cloud probes use synthetic fixtures and deny tool execution. No paid model is
selected. The official Linux control uses a fixture under `/tmp` to avoid
project ancestor instructions.

The user authorised a basic local model as an alternative. The pinned
[Qwen3 0.6B Q8_0 model](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/blob/23749fefcc72300e3a2ad315e1317431b06b590a/Qwen3-0.6B-Q8_0.gguf)
is 639,446,688 bytes; revision and checksum are in
`reference/opencode-local-model-manifest.json`. A temporary Linux llama.cpp
server uses GPU offload zero, two CPU threads, a localhost-only listener and a
ten-minute expiry. The guest reaches it through QEMU's user network at
`10.0.2.2:18082`. No existing model service is changed.

A direct bounded chat request returned `OK`. The first native OpenCode request
returned only empty thinking markers despite exit 0. That is recorded as an
unsuccessful semantic test in `results/20261014-headless-port/history/opencode-guest-local-model-attempt1.log`.
The diagnostic relay captured an assistant prefill declaring the step budget
exhausted: the initial probe set `steps: 1`, which exhausted it before the first
request. Changing that configuration to four steps fixed the semantic failure.
Native Haiku OpenCode then returned exactly `OK`; see
`results/20261014-headless-port/opencode-guest-local-model.log`. A Linux control returned the same
text. This is a real local-model response, not a simulated provider.

The bounded model-directed editing test did not complete the fix (semantic exit 2). It permits reads only of
fixture `.mjs` files, editing only `add.mjs`, and running only `node test.mjs`.
Its first configuration used absolute permission resources, but OpenCode uses
relative resources inside a location. That interrupted attempt is preserved;
the corrected test also disables formatters/LSP for the isolated fixture.
The real model successfully called Haiku's read tool and shell tool. Its edit
arguments were wrong (`oldString: "+"`, `newString: "b"`), and the edit tool
rejected them. It tried to overwrite the test file with `console.log('OK')`,
which the single-file edit policy denied. The untouched assertions then failed
as expected. The model repeated its invalid edit and ended with an unfulfilled
promise to fix the file. We record this as a model-task failure, not a successful
coding session. Evidence: `results/20261014-headless-port/opencode-guest-agent-model.log`.

This establishes real model-to-tool dispatch, failure feedback and enforcement
of edit permissions on Haiku. It does not yet establish a successful model-led
mutation, passing tests, or general coding usefulness. A more capable coding
model and a resumed conversation remain the next validation needs.

## Remaining work

- Complete a successful model-driven edit/test task with a more capable model, then validate a resumed conversation.
- Use a sufficiently capable model for coding quality evaluation; 0.6B is a
  connectivity fixture.
- Resolve native search and watcher limitations; watching currently logs an
  unsupported-platform error without blocking the tested APIs.
- Package and validate a portable shell/search dependency set as needed.
The complete archive and launcher were validated in a fresh guest directory.
Native ripgrep 14.0.1-1 was installed; OpenCode's existing ripgrep/fuzzysort fallback
found `add.mjs`. File read/write, shell assertions and stored-session restart
checks all passed from that extracted package. Evidence:
`results/20261014-headless-port/opencode-guest-package-check.log` and
`results/20261014-headless-port/opencode-guest-package-api.log`.

Scripts under `tools/opencode-port/` (removed on 23 October 2026, in Git history) reproduced the runtime, baseline, patched
launch, API and model probes. They use the repository's localhost transfer
server and approved cardless VM. Mechanical transfer URL and initial default
log-directory failures were corrected; the underlying feature failures remain
recorded separately. The CLI prototype is not yet a completed general-purpose
Haiku coding agent.

## Repository separation

On 14 October 2026 the port moved into the independent `opencode-haiku`
repository. Its source archive, installed dependency tree, Bun, manifests,
patches, scripts and evidence moved with it. The stopped installed cardless VM,
EFI variables and ISO were copied into independent ignored files. This keeps
OpenCode independent of the Haiku LLM/runtime-contract repository. The optional
model endpoint can be any compatible separately selected server; the earlier
CPU inference test used the original repository's llama.cpp build. Nothing in
OpenCode's build or startup requires that build. Original logs retain the paths
where each test actually ran.
