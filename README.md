# OpenCode for Haiku

A port of OpenCode to x86_64 Haiku. It gives the headless CLI, the full terminal
interface (TUI) and the browser interface (WebPositive), with terminal panes, clipboard
paste and shared sessions. It runs on Node 24. It needs an OpenAI-compatible model
endpoint, for example a llama.cpp server or a cloud provider.

## Disclaimer

This is research code. It is not production code.

I made it as part of a project that tests the Tesla K40c hardware under Haiku. I like
unusual operating systems, and Haiku is an interesting one. That is the main reason this
project exists.

The code is not meant for inclusion in Haiku, HaikuPorts or any other Haiku project.
AI coding agents generated most of it ("vibe coding"). I understand that the Haiku
project does not want such packages, and I do not submit them. If the research is
useful to someone, I am glad.

A second question drives the work: can Haiku be a suitable sandbox for AI coding
agents? I do not know of specific vulnerabilities of Haiku for this use. An uncommon
system can also be a useful barrier. This is a question to test, not a claim of
security. The target use is agents that test scientific software, such as GNU Octave,
scientific Python and perhaps R.

Use it at your own risk. The license gives no warranty.

| | |
|---|---|
| Port version | `2.0.29-haiku.5` (upstream OpenCode `2.0.29`, commit `34d8ded0`) |
| Tested system | Haiku hrev60207 x86_64, Node 24.21.0-1 |
| Package | Release archive today. Haiku package recipe in `packaging/`, not built yet ([design/packaging.md](docs/design/packaging.md)). |
| State | [docs/STATUS.md](docs/STATUS.md) |
| License | MIT ([LICENSE](LICENSE)). Bundled upstream components keep their own licenses. |

## Installation

Read [docs/INSTALL.md](docs/INSTALL.md). In short: copy the archive and
`src/install.sh` into Haiku, then:

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
| `VERSION` | The port version. Build scripts read it. |
| `src/` | Shipped files: launcher, installer, self-test, Haiku shims (FFI, watch, HTTP, clipboard) |
| `build/` | Fetch, native build, bundle and packaging scripts. `build/guest/` runs in the VM. |
| `packaging/` | HaikuPorter recipe of the Haiku package |
| `patches/<upstream>/` | Patches against OpenCode, OpenTUI, Zig, Koffi, node-pty, opencode-pty and Ghostty, with a `series` file each |
| `tests/unit/` | Host tests (`make test`) and guest unit fixtures |
| `tests/acceptance/` | Guest workflows and probes. `tests/acceptance/vm/` holds the VM job scripts. |
| `tools/secrets/` | Key handling and secret scan |
| `reference/` | Input pins (`INPUTS.json`) and provenance records |
| `results/` | Evidence, one folder per run (`results/README.md`) |
| `examples/` | Example configuration and the cloud coding task |

Not tracked: `cache/`, `source/`, `vm/`, `logs/`, `share/`, `dist/` (archives, sources, VM disks).

Checks: `make check` (unit tests, lint, shell syntax, secret scan). Build: `make fetch`, then
[docs/BUILD.md](docs/BUILD.md), then `make dist`. The VM tools come from the `haiku-k40c`
repository (`$HAIKU_K40C_ROOT`, default `../haiku-k40c`).

## Limits of the evidence

Functional checks ran in cardless Haiku VMs (TCG and KVM). These are CPU-only results.
They are not evidence of K40c GPU support. Reliable autonomous coding with a local model
is not shown. [docs/KNOWN-LIMITATIONS.md](docs/KNOWN-LIMITATIONS.md) lists the open limits.
