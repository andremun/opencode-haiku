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
backend, as shown in section 9 below. Open that link in
WebPositive. Avoid starting a second background service against the same profile.
Ctrl-C closes the TUI; stop the backend separately when finished.

Text clipboard paste and packaged TUI/browser terminal controls pass in
Haiku.5. Clipboard images/primary selection and recursive watching remain
unavailable. See [Haiku.5 acceptance](history/20261015-haiku5-acceptance.md) for measured coverage
and limitations, and [the development guide](DEVELOP.md) for llama.cpp,
dependencies and model download, and [the build guide](BUILD.md) for source rebuilding.

## Full configuration reference

Split from `T7610-HAIKU-SETUP.md` on 23 October 2026. Section numbers are those of that guide. "Section N" refers to them: sections 1 to 7, 11 and 12 are in [DEVELOP.md](DEVELOP.md), sections 8 and 9 in [INSTALL.md](INSTALL.md), section 10 in [BUILD.md](BUILD.md).

### 8. Install OpenCode from the repository's prepared runtime

On Linux, locate `share/opencode-haiku-tui-2.0.29-haiku.5.tar.gz` and read
`results/opencode-tui-package.json`. Transfer the archive, the repository's
`tools/tui-port/install.sh`, and the example config below to Haiku.

The current archive is 53,682,981 bytes, SHA-256:
`b9970cd8592ad48050c9340579c6d3e4d3d7c326e7e603cb921afbea481cf8f2`.
After any rebuild, use the newly generated manifest rather than this snapshot.

**Haiku, from the directory containing the transferred files:**

```sh
sh install.sh opencode-haiku-tui-2.0.29-haiku.5.tar.gz \
  b9970cd8592ad48050c9340579c6d3e4d3d7c326e7e603cb921afbea481cf8f2 \
  /boot/home/opencode-haiku-2.0.29-haiku.5
OC=/boot/home/opencode-haiku-2.0.29-haiku.5
"$OC/opencode" --version
export OPENCODE_HAIKU_KOFFI="$OC/koffi"
export NODE_OPTIONS="--require=$OC/haiku-loader.cjs"
export LIBRARY_PATH=/boot/system/lib
node "$OC/selftest.cjs"
unset NODE_OPTIONS OPENCODE_HAIKU_KOFFI
```

Expected self-test: `SELFTEST_PASS: native FFI, watcher, clipboard read, clean release`.
The installer refuses an existing destination; install upgrades into a new
directory. The launcher configures Haiku FFI, native clipboard, watcher and HTTP
fallbacks, and paths for both PTY backends. Launch through `opencode`, not by
running the bundle without its environment. Runtime requirements are Node 24+,
Haiku system libraries, and ripgrep for efficient search; compiler toolchains
are not needed for ordinary use of the installed archive.

### 9. Configure a workspace, shared backend, TUI and browser

The supplied [text-only configuration](../examples/haiku-local-chat.json) matches
the verified endpoint and disables tools for the initial inference test.
Copy it as `opencode.json` in a disposable workspace:

```sh
mkdir -p /boot/home/opencode-work
cp /boot/home/opencode-haiku-src/examples/haiku-local-chat.json \
  /boot/home/opencode-work/opencode.json
mkdir -p /boot/home/opencode-profile/data /boot/home/opencode-profile/config \
  /boot/home/opencode-profile/cache /boot/home/opencode-profile/state
```

In **each OpenCode Terminal**, set the same profile and backend credential:

```sh
OC=/boot/home/opencode-haiku-2.0.29-haiku.5
export XDG_DATA_HOME=/boot/home/opencode-profile/data
export XDG_CONFIG_HOME=/boot/home/opencode-profile/config
export XDG_CACHE_HOME=/boot/home/opencode-profile/cache
export XDG_STATE_HOME=/boot/home/opencode-profile/state
export OPENCODE_PASSWORD='replace-with-your-own-local-test-password'
cd /boot/home/opencode-work
```

First Terminal:

```sh
"$OC/opencode" serve --hostname 127.0.0.1 --port 18083
```

Second Terminal:

```sh
"$OC/opencode" --server http://127.0.0.1:18083
```

Ask `Reply with OK only.` Then exit the TUI with Ctrl-C and restore using:

```sh
"$OC/opencode" --server http://127.0.0.1:18083 --continue
```

For WebPositive, issue a pairing code **on the same running backend**:

```sh
curl -fS -X POST -u "opencode:$OPENCODE_PASSWORD" \
  http://127.0.0.1:18083/api/pair -o /tmp/opencode-pair.json
node -e 'const fs=require("node:fs");const r=JSON.parse(fs.readFileSync("/tmp/opencode-pair.json","utf8"));const code=r.code??r.data?.code;if(!code)throw Error("Missing pairing code");console.log("http://127.0.0.1:18083/auth/connect/"+code)'
rm /tmp/opencode-pair.json
```

Open the printed link in WebPositive inside Haiku. Codes expire after five
minutes and work once. Do not save credentials/pairing codes in Git. This API
procedure targets the explicit shared `serve` process. The upstream `opencode
pair` command ensures a background service; do not invoke it casually alongside
an already owned profile, because it may create a second backend.

Open the TUI-created session in the browser, submit a follow-up, and check that
the same session updates in the TUI. One SQLite profile must have **one backend**.
The TUI and GUI are clients of it. Stop the backend separately with Ctrl-C.

For a real coding experiment, copy the text-only config, enable the model's
`capabilities.tools`, select the `build` agent, set output limit/body max_tokens
to 256, and replace the deny-all rule with narrow read/edit/shell permissions
for a disposable workspace. Preserve the text-only control config. Inspect
`tools/tui-port/coding-workflow.mjs` for the measured bounded fixture and its
permission syntax. That runner currently assumes the development guest paths
and transfer service; it is not a portable one-command T7610 installer.
