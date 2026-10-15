# OpenCode on Haiku

## Full TUI and browser GUI

The full upstream OpenCode TUI and browser GUI are now tested in native Haiku
with a native llama.cpp CPU server and Qwen3 1.7B Q4_K_M. Session recovery and
live updates between the two interfaces work. Coding quality in the small-model
test was poor; that was not an acceptance failure.

See [the acceptance report](docs/TUI-ACCEPTANCE.md) for measured evidence,
reproduction and remaining feature limits. The self-contained runtime archive
is in ignored `share/opencode-haiku-tui-2.0.29-haiku.4.tar.gz`; its exact hashes
are in `results/opencode-tui-package.json`. The tooling is in `tools/tui-port/`.
The interface tests use one shared OpenCode backend per Haiku SQLite profile.

A persistent cardless KVM Haiku VM and the complete T7610 rebuild/test run are
described in [docs/KVM-VM.md](docs/KVM-VM.md) and
[docs/T7610-KVM-RESULTS-20261015.md](docs/T7610-KVM-RESULTS-20261015.md).


Native OpenCode headless CLI, full TUI and browser GUI port using Haiku Node 24. This repository is
independent of `haiku-k40c-llm` and `llm-server`. It builds OpenCode itself; a model
API is a separately selected endpoint.

Read [status](docs/STATUS.md) and the [port report](docs/OPENCODE-HAIKU-PORT.md).

```sh
sh tools/opencode-port/build.sh
```

The generated archive lives in ignored `share/` and includes a launcher, bundle,
assets and upstream MIT license. On Haiku, install `nodejs24` and `ripgrep`, then
extract the archive and run `./opencode --help`. Use `run --standalone` for an
isolated private server.

Measured: native launcher, files, fallback file search, shell execution, stored
session recovery and real local-model text. Model-driven read/shell calls work,
but the tiny model failed to fix the synthetic coding task. The full TUI and nonrecursive polling watches now work; native clipboard now passes, and native PTY backends pass their own tests.
Combined terminal integration remains pending. OpenCode's anonymous free service rejected both the
port and official Linux control. No paid models, physical GPUs, host sudo or
existing model-service changes were used.

`tools/app_vm.py` controls only this repository's cardless VM. Virtual disks,
source archives, dependencies, models and logs remain ignored by Git. A copied
installed VM is a local development convenience; source and evidence pins live
in `reference/` and `results/`.

See [installation](docs/INSTALL.md) and [continuation results](docs/CONTINUATION-OUTCOME.md) for fresh native/Linux controls, text clipboard and remaining terminal work.

Full setup: [T7610 Haiku installation and source build](docs/T7610-HAIKU-SETUP.md).

Review of the T7610 results and runner corrections: [commit review](docs/T7610-COMMIT-REVIEW.md).
