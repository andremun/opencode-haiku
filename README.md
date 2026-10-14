# OpenCode on Haiku

Native headless OpenCode CLI port using Haiku Node 24. This repository is
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
but the tiny model failed to fix the synthetic coding task. OpenTUI/PTY and
watching remain unported. OpenCode's anonymous free service rejected both the
port and official Linux control. No paid models, physical GPUs, host sudo or
existing model-service changes were used.

`tools/app_vm.py` controls only this repository's cardless VM. Virtual disks,
source archives, dependencies, models and logs remain ignored by Git. A copied
installed VM is a local development convenience; source and evidence pins live
in `reference/` and `results/`.
