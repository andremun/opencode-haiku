# OpenCode for Haiku

A port of OpenCode to x86_64 Haiku. It gives the headless CLI, the full terminal
interface (TUI) and the browser interface (WebPositive), with terminal panes, clipboard
paste and shared sessions. It runs on Node 24. It needs an OpenAI-compatible model
endpoint, for example a llama.cpp server or a cloud provider.

| | |
|---|---|
| Port version | `2.0.29-haiku.5` (upstream OpenCode `2.0.29`, commit `34d8ded0`) |
| Tested system | Haiku hrev60207 x86_64, Node 24.21.0-1 |
| Package | Release archive today. Haiku package (`.hpkg`) planned ([design/packaging.md](docs/design/packaging.md)). |
| State | [docs/STATUS.md](docs/STATUS.md) |
| License | MIT ([LICENSE](LICENSE)). Bundled upstream components keep their own licenses. |

## Installation

Read [docs/INSTALL.md](docs/INSTALL.md). In short: copy the archive and
`tools/tui-port/install.sh` into Haiku, then:

```sh
sh install.sh ARCHIVE.tar.gz SHA256 /boot/home/opencode-haiku
node /boot/home/opencode-haiku/selftest.cjs
```

The archive name and SHA-256 are in `results/opencode-tui-package.json`.

## Usage

Start one shared backend in the project folder, then attach the TUI:

```sh
/boot/home/opencode-haiku/opencode serve --hostname 127.0.0.1 --port 18083
/boot/home/opencode-haiku/opencode --server http://127.0.0.1:18083
```

Configure the model endpoint in the project `opencode.json`. Example:
[examples/haiku-local-chat.json](examples/haiku-local-chat.json).
Keep API keys outside the repository ([docs/SECRETS.md](docs/SECRETS.md)).

## Documentation

| Document | Content |
|---|---|
| [docs/INSTALL.md](docs/INSTALL.md) | Install, configure, start the backend, attach the TUI and the browser |
| [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) | The checks a release must pass, with the last result of each |
| [docs/KNOWN-LIMITATIONS.md](docs/KNOWN-LIMITATIONS.md) | What does not work, and the workarounds |
| [docs/BUILD.md](docs/BUILD.md) | Build the archive from pinned sources |
| [docs/DEVELOP.md](docs/DEVELOP.md) | Test VM, guest setup, local llama.cpp endpoint, test runs, troubleshooting |
| [docs/design/](docs/design/) | Architecture, packaging design and target layout |
| [docs/decisions/](docs/decisions/) | Architecture decision records |
| [docs/history/](docs/history/README.md) | Dated reports and old status text |
| [CHANGELOG.md](CHANGELOG.md) | Port versions and changes |

## Layout

| Path | Content |
|---|---|
| `tools/tui-port/` | Runtime shims, launcher, installer, build scripts and test probes of the full port (split in Phase 2, [design/layout.md](docs/design/layout.md)) |
| `tools/opencode-port/` | The earlier headless port (`haiku.1`) and its probes |
| `tools/kvm-run/` | Job scripts for the persistent test VM |
| `tools/secrets/` | Key handling and secret scan |
| `reference/` | Source pins, input manifests and patches against upstream components |
| `results/` | Evidence, one folder per run (`results/README.md`) |
| `examples/` | Example configuration and the cloud coding task |

Not tracked: `cache/`, `source/`, `vm/`, `logs/`, `share/` (archives, sources, VM disks).

## Limits of the evidence

Functional checks ran in cardless Haiku VMs (TCG and KVM). These are CPU-only results.
They are not evidence of K40c GPU support. Reliable autonomous coding with a local model
is not shown. [docs/KNOWN-LIMITATIONS.md](docs/KNOWN-LIMITATIONS.md) lists the open limits.
