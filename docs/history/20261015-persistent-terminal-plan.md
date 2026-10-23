# Persistent terminal status

15 October 2026. The portability and packaged functional acceptance stages
are complete in the local cardless TCG VM. Standard Haiku.5 builds apply the
Ghostty VT renderer patch, resolving the packaged Haiku.4 TUI crash.

Both terminal APIs and both real UI renderers pass I/O, UTF-8, resize,
reconnect/reload and child exit controls. The TUI also passes native clipboard
paste. Full 54-test daemon, formatting and Clippy output is saved. See
[HAIKU5-ACCEPTANCE.md](20261015-haiku5-acceptance.md) for exact coverage and limitations.

The T7610 result has separate evidence and a full-suite capture gap; the new
TCG result does not fill it. Repeat the improved tests on that machine using
[T7610-NEXT-RUN.md](20261015-t7610-next-run.md). Native source/build and artifact pins
remain in reference/ and results/. No GPU or host sudo is involved.
