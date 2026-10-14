# Status

Updated 15 October 2026 (Australia/Melbourne).
Independent repository: `opencode-haiku`. No sibling repository is needed to
run the installed runtime or follow the self-contained T7610 guide.

## Current outcome

Native Haiku full OpenCode TUI and browser GUI have run with native llama.cpp
CPU inference. Current combined build: **2.0.29-haiku.4**. Its build succeeds;
its newly integrated terminal panels still require end-to-end acceptance.

Pinned OpenCode: 34d8ded0c58dd66808c1d60e081e8c66da12a896; OpenTUI 0.5.17;
Bun 1.4.2 build host; Haiku hrev60207 with Node 24.21.0-1; patched Koffi 3.3.3;
patched Zig 0.16.0. Source and output provenance is under reference/ and results/.

## Verified

- Earlier full TUI prompt/CPU response, clean exit, continuation, WebPositive
  pairing and shared-session updates passed. See TUI-ACCEPTANCE.md.
- Three fresh Qwen3 1.7B requests match Linux output, including Python addition
  and arithmetic. Different cache states make these functional controls, not
  cold-start performance comparisons.
- Native clipboard helper, OpenTUI factory and actual TUI paste passed.
- Native file/read/write/search, shell test and saved-session recovery passed.
- Checksum installer preservation/cleanup controls and fresh Haiku.3 install,
  FFI/watcher/clipboard self-tests passed.
- Explicit unlimited HTTP waits and AbortSignal controls pass on Linux/Haiku;
  this fixes Node's default timeout on upstream timeout:false wait requests.
- Matching upstream persistent daemon 0.2.0 at
  878aa26ab1916f8d41a0ccb90d55a372d01abf69 builds with native Rust 1.94.1.
  All 54 upstream tests, formatting and Clippy pass. Ghostty static scalar VT
  parser is pinned at ab0b9da9e88fcb4b0533a1854e84628f663930af.
- Browser's separate native Node PTY binding passes I/O, UTF-8, resize and exit.
- Haiku.4 combines these inputs and builds successfully; package checksum is
  in results/opencode-tui-package.json.
- Complete T7610 installation/build/test guide, standalone llama patches and
  example provider config are committed. See T7610-HAIKU-SETUP.md.

## Pending and unsuccessful results

- Combined Haiku.4 daemon/TUI/browser terminal integration is pending. The
  prior legacy API test failed loading the Linux PTY asset; the new bundle
  preserves the native override. That correction has not yet passed API/UI tests.
- A real coding fixture reached its 45-minute deadline during prompt processing,
  with no edit/tool calls. Recorded as an emulated resource/time limitation,
  not an observed incorrect patch or coding-quality acceptance failure.
- Initial concurrent 4-GiB workloads caused severe memory pressure. The owned
  cardless VM was recovered using a preserved disk/EFI copy and 8 GiB, still
  two TCG vCPUs. Sequential implementation controls pass after recovery.
- This host has no /dev/kvm; an accelerated T7610 run has not been performed.
- The early Rust-version blocker was incorrect: native package metadata and
  installed Rust 1.94.1 supersede the older inspected source recipe.
- Earlier executable-mode, five-minute HTTP timeout, addon instruction-set,
  SQLite duplicate-owner, manual GUI login and EOF issues retain failed evidence
  and their corrections. NUL-containing partial capture is excluded from Git
  and recorded by hash. See CONTINUATION-OUTCOME.md and TUI-ACCEPTANCE.md.

## Evidence boundaries and resources

No host sudo, physical GPU, host driver or existing host model service was used.
All inference evidence is CPU/cardless; no K40c compute support is established.
Recursive watching, clipboard images/primary selection and a native Electron
application are not implemented. General coding usefulness remains unproven.

The independent 8-GiB cardless VM remains running. Owned native model and
isolated Linux CPU control servers were stopped. The local transfer service may
remain running for continuation. Archives, models, SDKs, caches and disks are
ignored build inputs; a Git clone does not contain the prepared runtime archive.
No push was performed. See INSTALL.md and T7610-HAIKU-SETUP.md for installation.
