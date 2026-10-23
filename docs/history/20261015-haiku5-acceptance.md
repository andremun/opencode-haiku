# Haiku.5 terminal integration and manual performance handoff

15 October 2026 (Australia/Melbourne). **The packaged TUI terminal crash is
fixed.** The standard build now enables Ghostty VT for Haiku, rather than
requiring an experimental replacement library. Both the packaged TUI pane and
WebPositive terminal panel were exercised visually and through their native APIs.

## Platform and archive

This run used the existing independent, cardless **TCG** Haiku hrev60207 VM,
2 qemu64 vCPUs, 8 GiB. This host has no `/dev/kvm`. The T7610 is accessible only
manually, as confirmed by the user; no accelerated measurement is claimed here.
No host sudo, GPU access, host driver or existing host model-service change occurred.
The driver repository was inspected read-only in response to a feasibility
question; no driver task was started or changed.

- Runtime: `2.0.29-haiku.5`, 53,682,981 bytes.
- Archive SHA-256: `b9970cd8592ad48050c9340579c6d3e4d3d7c326e7e603cb921afbea481cf8f2`.
- Renderer SHA-256: `d0eed90c5ff51a1f2c600f87bed15941d922d213a372032fdc229d05b6074fe7`.
- Bundle SHA-256: `2db5b1b11f608c325e299d9d61cdef4a630d8ea305dc3e199835df741872d0c1`.
- Pinned source/patch/SDK/addon records: `reference/TUI-PORT-INPUTS.json` and
  `results/native-build-inputs.json`. The local SDK/addon match the explicitly
  recorded original hashes, not the rebuilt T7610 variants. Checks remain enabled.
- Build: `sh tools/tui-port/build_bundle.sh`; full log `results/20261015-haiku5-renderer/haiku5-build.log`.
  The renderer patch is now applied by build_native.sh and packaging checks for it.
- All runtime files, including both native terminal backends, are in the ignored
  archive; native hashes are in `results/opencode-tui-package.json`. The daemon's
  MIT notice is now included as well.

The archive was transferred, checksum-installed into a fresh
`/boot/home/opencode-haiku5`, and tested there. Prior installations were preserved.
No new model inference was needed for these terminal controls. Native llama.cpp
and real-model GUI/TUI inference evidence from earlier runs remains separate.

## Measured checks

| Check | Outcome and evidence |
|---|---|
| Fresh install / FFI / polling watch / clipboard read | Pass, exit 0: `haiku5-install-selftest.log` |
| Native upstream daemon suite | All 54 tests, formatting and Clippy pass with full output and exit 0: `haiku5-native-terminal-suite.log` |
| Actual file/shell/session controls | Pass, including backend restart: `haiku5-api-workflow-api.log` |
| Browser's separate native PTY API | Pass: `haiku5-legacy-pty-api-api.log` |
| Persistent daemon through bundled server | Pass: UTF-8, input, resize, snapshot/read, reconnect/replay, child exit 5, cleanup/shutdown: `haiku5-persistent-terminal-api-run.log` |
| Packaged TUI pane | Opens without the old crash; real shell input and UTF-8 output: `haiku5-tui-terminal-io.png` |
| TUI window resize | Child stty size changes 24x38 to 74x80: `haiku5-tui-terminal-resize.png` |
| TUI session reconnect | Earlier output restored; another client accepts new input on the same terminal: `haiku5-tui-terminal-reconnect.png` |
| TUI child exit / clipboard | `exit 3` closes the pane without crashing; native Alt-V inserts the exact marker into the prompt without inference: `haiku5-tui-child-exit-clipboard.png` |
| TUI cleanup | No persistent terminals remain: `haiku5-tui-terminal-cleanup.log`; TUI exit 0 |
| WebPositive terminal | Opened through `/terminal`, command output and UTF-8 visible: `haiku5-browser-terminal-io.png` |
| Browser resize | Child dimensions change 89x145 to 20x47: `haiku5-browser-terminal-resize.png` |
| Browser full reload | Prior output restores and the shell accepts new input: `haiku5-browser-terminal-reload.png` |
| Browser child exit / cleanup | Exit 7 delivered, dock closes; API records exited status, then explicit deletion leaves an empty list: `haiku5-browser-child-exit.log`, `haiku5-browser-cleanup.log` |
| Host regression controls | Nine groups pass, including failure propagation, immutable coding tests and host-platform guards: `haiku5-host-regressions.log` |

The native suite rerun produced its own newly built daemon binary. The archive
contains the earlier tested binary from the same pinned source and parser;
the bundled daemon was separately exercised by the server API controls above.
This full TCG capture does not retroactively fill the missing full T7610 capture.

## Corrections, limits and unsuccessful intermediate observations

- The TUI terminal shortcut is session-specific. On an empty home screen it did
  not open a terminal; creating and opening a saved session enabled it.
- Large Terminal windows briefly showed old paint during reconnection. A fresh
  window showed the restored terminal, and both clients saw new output.
- The browser terminal initially appeared blank while its WASM renderer loaded
  under TCG. It subsequently showed a live shell; no browser fallback patch was
  needed. `/terminal` reliably opened the panel where the shortcut did not.
- One fast synthetic command after browser reload omitted its space, producing
  a shell command-not-found response. That response establishes a live connection,
  not a successful echo. The subsequent `exit 7` was delivered correctly. This
  run does not establish keyboard reliability under arbitrary emulation load.
- Native clipboard paste was repeated with a clean prompt and recorded as one
  exact marker. Original clipboard content was restored. Writing an empty stream
  through the helper failed; the explicit clear operation restored the originally
  empty clipboard. Empty-stream write remains a small known helper limitation.
- Browser black session-tab styling persists. Recursive watching, clipboard
  images/primary selection and a native Electron application remain unsupported.

## Performance and coding work prepared for the T7610

[T7610-NEXT-RUN.md](20261015-t7610-next-run.md) contains the manual pull/build/stage/run
workflow. Added tools build separate baseline and guarded Ivy Bridge AVX/F16C
profiles, benchmark batches 128/32 and 512/128, and keep source/binary/command
provenance. These binaries and performance measurements have **not** run here.
No speed improvement or recommendation to adopt a profile is claimed yet.

The coding fixture now uses eight steps by default and a fresh private fixture
and profile each run. Acceptance requires an unchanged immutable test, an actual
completed agent shell call running `node test.mjs`, and a passing independent
execution. It records independent correctness separately if the agent omits its
test. Host positive/negative controls pass; a new real-model eight-step run is
still a manual T7610 experiment. The previous correct edit remains useful
but insufficient evidence of reliable autonomous coding.

Pinned OpenCode source already honours a custom agent system prompt. Removing
its remaining environment/tool context was not justified by these measurements;
no permission or workspace instructions were removed as a speed patch.

## Next external steps

Commit and push this continuation, then pull on the T7610. Rebuild there and run
its full-log native checks, CPU/batch matrix, direct inference controls and revised
coding fixture. Models, caches, archives and VM disks remain outside Git.
