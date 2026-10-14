# Persistent terminal progress and remaining acceptance

15 October 2026. The compiler/parser/daemon portability stage is complete.
The earlier proposed compiler bootstrap is unnecessary: native Rust 1.94.1
supports the required edition and target.

The matching daemon 0.2.0 revision and Ghostty parser are pinned in
reference/PTY-PORT-INPUTS.json. Native tests pass: 30 library, 5 parser-effects,
6 ownership, 3 observer, 1 rows and 9 service tests (54 total). Formatting and
Clippy pass. Haiku EOF reports EBADF even while the master descriptor remains
valid; the narrow Haiku correction checks descriptor validity before publishing
EOF. Child-exit and EOF events remain separate.

Browser terminals use a separate Node PTY binding. Its native input/output,
UTF-8, resize and exit controls pass. Haiku.4 includes both native backends,
preserves OPENCODE_NODE_PTY_PATH and enables the daemon only with an existing
native binary. See T7610-HAIKU-SETUP.md for full clean-source build instructions.
Historical generated daemon source archives predate the final test/EOF patches;
apply the three committed patches to pristine source for a final rebuild.

Remaining acceptance:

1. Install/checksum/self-test the combined Haiku.4 archive in a fresh directory.
2. Test the legacy browser PTY API with its actual native binding override.
3. Test persistent daemon integration through the bundled server and TUI.
4. Test browser terminal rendering, I/O, resize, exit, reconnect and cleanup.
5. Record the runtime/session recovery outcomes and any browser limitations.

Passing primitive or upstream daemon tests does not establish these UI results.
No host sudo, physical GPU or scope decision is required for the present work.
