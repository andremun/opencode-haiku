# Status

Updated 15 October 2026 (Australia/Melbourne).
Independent repository: `opencode-haiku`. No sibling repository is needed to
run the installed runtime or follow the self-contained T7610 guide.

## 2026-10-15 update: persistent KVM VM and T7610 run

A persistent, cardless **KVM** Haiku VM now exists on this Dell Precision T7610
(`vm/system.qcow2`, 2 vCPU, 8 GiB, `-cpu host`, two E5-2620 v2). See
[KVM-VM.md](KVM-VM.md). The complete rebuild from pinned sources and the guide's
tests are recorded in [T7610-KVM-RESULTS-20261015.md](T7610-KVM-RESULTS-20261015.md)
with evidence in `results/t7610-20261015-kvm-e5-2620v2/`.

- Rebuilt: llama.cpp b8861 CPU (tests pass), Koffi, clipboard helper, node-pty
  binding, PTY daemon 0.2.0 (54 tests, fmt, Clippy pass), Ghostty parser,
  OpenTUI renderer and the `2.0.29-haiku.4` archive (52,365,590 bytes,
  SHA-256 `131d42be...`). Several native hashes differ from the originals and are annotated.
- Fresh controls match the Linux and TCG outputs; KVM is about 3 times faster on
  the three direct requests. The first OpenCode TUI exchange still took 15 m 51 s
  (530-token system prompt at 0.74 tok/s), so no speed-up there is claimed.
- TUI prompt, clean exit, session restore, GUI pairing and live sharing in both
  directions pass. File, shell, session-persistence, browser-PTY and persistent
  daemon API tests pass.
- **The TUI embedded terminal pane fails as built** (renderer lacks Ghostty VT on
  Haiku). A one-line experimental patch, `reference/opentui-haiku-ghostty-vt.patch`,
  makes it work in a manual test; it is not yet in the build or archive.
- Not done: AVX or batch-size variants, TUI paste in the UI, browser terminal
  panel visually. Coding fixture: the model edited the source correctly (`a + b`) in 44 min 25 s but did not run the shell test, so the runner's semantic check is false.
- Nothing is committed or pushed. This run is a CPU/cardless result.

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
