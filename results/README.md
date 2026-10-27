# Results

One folder per run. Each folder has a `MANIFEST.json` with file sizes, SHA-256 hashes and the
documents that cite it. A `history/` subfolder holds attempt, progress and superseded logs.
All runs used cardless Haiku VMs. They are not GPU evidence.

| Folder | Content | Cited by (under `docs/`) |
|---|---|---|
| `20261014-headless-port/` | Headless OpenCode port (haiku.1) in the TCG VM: build, API probes, local and free model runs | history/20261021-status.md |
| `20261015-tui-port/` | Full TUI and browser port on Haiku CPU inference: FFI, TUI and GUI runs, native chat | history/20261015-tui-acceptance.md |
| `20261015-terminals-clipboard/` | Native clipboard, HTTP waits, PTY daemon and node-pty builds and tests | history/20261015-continuation-outcome.md |
| `20261015-haiku5-renderer/` | Haiku.5 with the Ghostty VT renderer: install, native suite, API, TUI and browser terminal checks | ACCEPTANCE.md, history/20261015-haiku5-acceptance.md |
| `20261015-t7610-kvm/` | First T7610 KVM run (E5-2620 v2) | history/20261015-t7610-kvm-results.md |
| `20261016-t7610-haiku5/` | Haiku.5 on the persistent KVM VM, CPU profiles, coding fixture | history/20261016-t7610-kvm-haiku5-results.md |
| `20261016-t7610-haiku5-production/` | Production-matching CPU build in the KVM VM | history/20261016-t7610-kvm-haiku5-results.md |
| `20261018-phase123/` | Continuation phases 1 to 3: browser panel, TUI resize and reconnect on KVM | history/20261018-phase-1-3-results.md |
| `20261018-cloud-task/` | Cloud coding task through the port and the official client | history/20261018-free-models-and-cloud-task.md |
| `20261019-runner-fixes/` | Offline runner controls | history/20261019-runner-fixes.md |
| `20261021-task-e/` | Native runner rerun, ten free cloud models, interactive TUI, second client and browser | ACCEPTANCE.md, history/20261021-task-e.md, history/20261021-interactive-cloud.md |
| `20261026-host-controls/` | `make check` on commit `80c49b2` (host controls H-01 to H-04, lint, secret scan), and `make test` without a `haiku-k40c` checkout | ACCEPTANCE.md, STATUS.md |

Two files stay at the top because the build scripts read and write them:
`native-build-inputs.json` and `opencode-tui-package.json`. Phase 2 replaces them with
`dist/MANIFEST.json` ([design/packaging.md](../docs/design/packaging.md)).

On 23 October 2026 the flat files were grouped by the commit that added them. One-byte
`.exit` files, empty files and byte-identical duplicate logs were removed. Each manifest
records them. Old names: [docs/history/README.md](../docs/history/README.md).
