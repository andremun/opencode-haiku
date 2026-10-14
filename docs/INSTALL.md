# Install and run on Haiku

Requires x86_64 Haiku and Node >=24. The tested system is hrev60207 with
Node 24.21.0-1. No Bun or Python runtime is needed to run OpenCode.

Use the archive name and SHA-256 from `results/opencode-tui-package.json`.
Copy that archive and `tools/tui-port/install.sh` into Haiku, then run:

```sh
sh install.sh ARCHIVE.tar.gz SHA256 /boot/home/opencode-haiku
export OPENCODE_HAIKU_KOFFI=/boot/home/opencode-haiku/koffi
export NODE_OPTIONS=--require=/boot/home/opencode-haiku/haiku-loader.cjs
export LIBRARY_PATH=/boot/system/lib
node /boot/home/opencode-haiku/selftest.cjs
```

Choose a new destination for upgrades; existing installations are preserved.
The model is separate. Configure your project's opencode.json with a reachable
OpenAI-compatible provider and model alias. The test configuration in this repo
is deliberately restrictive and is not a normal coding configuration.

Start one shared backend from your project directory:

```sh
/boot/home/opencode-haiku/opencode serve --hostname 127.0.0.1 --port 18083
```

In another Terminal, enter the same project directory and attach:

```sh
/boot/home/opencode-haiku/opencode --server http://127.0.0.1:18083
```

Use `opencode pair --help` for the supported one-time browser pairing command;
open its link in WebPositive. Both interfaces use the same backend and sessions.
Do not start two backends against one SQLite state profile. Ctrl-C closes the
TUI; stop the backend separately when finished.

Text clipboard is native. Clipboard images and recursive watching remain
unavailable. Native terminal backends pass their own tests; combined Haiku.4
embedded terminal integration is still pending. Ordinary file and bounded shell tools
are separate from embedded terminal support. The earlier acceptance report
records tested browser/session behaviours and environment limits.

For the complete llama.cpp, dependencies, model and mixed-platform source-build
procedure, read [the T7610 setup guide](T7610-HAIKU-SETUP.md).
