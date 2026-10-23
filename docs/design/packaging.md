# Packaging design

Target: a user installs OpenCode on Haiku with `pkgman` and gets a known, tested version.
Decision: [ADR 002](../decisions/002-haiku-package.md).

## 1. Version

One file `VERSION` holds the port version, for example `2.0.29-haiku.5`. The build scripts,
the packager, the launcher, the manifest and the recipe read it. A new port release increments
the `haiku.N` suffix. A new upstream version changes the first part.

## 2. Inputs

`reference/INPUTS.json` lists every upstream input with its URL, version, SHA-256 and license.
The inputs are OpenCode, OpenTUI, Koffi, node-pty, node-addon-api, opencode-pty, Zig,
Bun (Linux build only), the Haiku SDK export and Node on Haiku. It replaces
`TUI-PORT-INPUTS.json`, `PTY-PORT-INPUTS.json`, `CONTINUATION-INPUTS.json`,
`opencode-port-manifest.json` and `TUI-MODEL.json`.

Patches move to `patches/<upstream>/NNNN-title.patch` with a `series` file for each upstream.

## 3. Build stages

| Target | Runs on | Output |
|---|---|---|
| `make fetch` | Linux | `cache/` with hash-checked archives |
| `make patch` | Linux | Patched sources in `source/` |
| `make native` | Haiku VM jobs, or a cross build where one exists | `cache/native/`: Koffi addon, `opencode-pty`, `node-pty`, `haiku-clipboard`, `libopentui.so`, with hashes |
| `make bundle` | Linux (Bun) | `opencode.mjs` and assets |
| `make dist` | Linux | `dist/opencode-haiku-<version>-x86_64.tar.gz`, `dist/SHA256SUMS`, `dist/MANIFEST.json` |
| `make hpkg` | Haiku VM | `dist/opencode_haiku-<version>-1-x86_64.hpkg` |

Today the native parts are built in the guest and copied into `cache/` by hand
(`tools/tui-port/package.py` stops with "Export the final guest-built Koffi addon first").
`make native` replaces this hand step.

## 4. Haiku package

`packaging/opencode_haiku-<version>.recipe` (HaikuPorter):

- `SOURCE_URI`: the release tar.gz, with its SHA-256.
- `REQUIRES`: `haiku`, `nodejs24`.
- Install tree: `apps/opencode/` (bundle, shims, native parts, `licenses/`) and a `bin/opencode` launcher.
- `TEST`: run the self-test.

## 5. Install paths

| Form | Command | Location |
|---|---|---|
| `.hpkg` | `pkgman install opencode_haiku` | system packages |
| tar.gz | `sh install.sh ARCHIVE SHA256 NEW_FOLDER` | a new user folder. Existing installs stay. |

## 6. Self-test

`opencode selftest` replaces `node selftest.cjs`. It checks the Node version, the Koffi load,
a PTY spawn, the clipboard helper and the renderer library. Exit 0 means all passed.

## 7. Release

A GitHub release for each version holds the tar.gz, the `.hpkg`, `SHA256SUMS`, `MANIFEST.json`
and the acceptance summary. A release needs a recorded pass of the checks in
[ACCEPTANCE.md](../ACCEPTANCE.md) in `results/YYYYMMDD-release-<version>/`. Archives never enter Git.

`dist/MANIFEST.json` replaces `results/opencode-tui-package.json` and
`results/native-build-inputs.json`.

## 8. Licenses

The archive keeps every upstream license under `licenses/`. `THIRD-PARTY-NOTICES.md` is
generated from `reference/INPUTS.json`.
