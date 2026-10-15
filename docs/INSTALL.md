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

Issue a one-time browser pairing code through `POST /api/pair` on this same
backend, as shown in section 9 of T7610-HAIKU-SETUP.md. Open that link in
WebPositive. Avoid starting a second background service against the same profile.
Ctrl-C closes the TUI; stop the backend separately when finished.

Text clipboard paste and packaged TUI/browser terminal controls pass in
Haiku.5. Clipboard images/primary selection and recursive watching remain
unavailable. See [Haiku.5 acceptance](HAIKU5-ACCEPTANCE.md) for measured coverage
and limitations, and [the complete guide](T7610-HAIKU-SETUP.md) for llama.cpp,
dependencies, model download and source rebuilding.
