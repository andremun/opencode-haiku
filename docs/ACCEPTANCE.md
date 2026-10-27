# Acceptance

A release of the port must pass these checks on the tested Haiku system. Each row names
the last result and its evidence folder under `results/`. The checks ran in cardless
Haiku VMs. They are not GPU evidence.

## Install and runtime

| ID | Check | Last result | Evidence |
|---|---|---|---|
| A-01 | Install from the archive with checksum, into a new folder | Pass, 2026-10-15 (TCG), 2026-10-16 (KVM) | `20261015-haiku5-renderer/haiku5-install-selftest.log`, `20261016-t7610-haiku5/` |
| A-02 | Self-test: FFI, polling watch, clipboard read | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-install-selftest.log` |
| A-03 | Native terminal daemon: 54 upstream tests, format and Clippy | Pass, 2026-10-15 and 2026-10-16 | `20261015-haiku5-renderer/haiku5-native-terminal-suite.log` |
| A-04 | File, shell and session API controls, backend restart | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-api-workflow-api.log` |
| A-05 | Persistent terminal API: UTF-8, input, resize, snapshot, reconnect, child exit, cleanup | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-persistent-terminal-api-run.log` |
| A-06 | Browser native PTY API | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-legacy-pty-api-api.log` |

## TUI

| ID | Check | Last result | Evidence |
|---|---|---|---|
| T-01 | Terminal pane opens, shell input, UTF-8 output | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-tui-terminal-io.png` |
| T-02 | Window resize changes the child size | Pass, 2026-10-15 (TCG), 2026-10-18 (KVM) | `20261015-haiku5-renderer/haiku5-tui-terminal-resize.png`, `20261018-phase123/` |
| T-03 | Session reconnect restores output and accepts input | Pass, 2026-10-15, 2026-10-18 | `20261015-haiku5-renderer/haiku5-tui-terminal-reconnect.png`, `20261018-phase123/` |
| T-04 | Child exit closes the pane without a crash | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-tui-child-exit-clipboard.png` |
| T-05 | Native clipboard paste (Alt-V) | Pass, 2026-10-15 | same |
| T-06 | Cleanup leaves no persistent terminals | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-tui-terminal-cleanup.log` |
| T-07 | Second TUI attaches to a live session. Messages appear live in both. | Pass, 2026-10-21 | `20261021-task-e/interactive/` |

## Browser (WebPositive)

| ID | Check | Last result | Evidence |
|---|---|---|---|
| B-01 | Terminal panel through `/terminal`: output and UTF-8 | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-browser-terminal-io.png` |
| B-02 | Resize | Pass, 2026-10-15, 2026-10-18 (KVM) | `20261015-haiku5-renderer/haiku5-browser-terminal-resize.png`, `20261018-phase123/` |
| B-03 | Full page reload restores output | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-browser-terminal-reload.png` |
| B-04 | Child exit and cleanup | Pass, 2026-10-15 | `20261015-haiku5-renderer/haiku5-browser-child-exit.log`, `haiku5-browser-cleanup.log` |
| B-05 | Browser opens the TUI session and makes a verified edit | Pass, 2026-10-21 | `20261021-task-e/interactive/` |

## Model work

| ID | Check | Last result | Evidence |
|---|---|---|---|
| M-01 | 8-step coding fixture with a local CPU model: immutable test unchanged, agent runs `node test.mjs`, independent pass | `semantic_pass` true, 2026-10-16 and 2026-10-21 (Ivy Bridge build) | `20261016-t7610-haiku5/`, `20261021-task-e/` |
| M-02 | Cloud CSV/report task, 15/15 independent tests, stricter acceptance | Pass with 9 of 10 free models, 2026-10-21 | `20261021-task-e/cloud-vm/` |

## Host controls

| ID | Check | Last result | Evidence |
|---|---|---|---|
| H-01 | `tests/unit/test_review_runners.py` | Pass, 3 tests, 2026-10-26 | `20261026-host-controls/` |
| H-02 | `tests/unit/test_t7610_runners.py` | 21 of 21 pass, 2026-10-26 (Node 24). Without a `haiku-k40c` checkout, 18 pass and 3 skip. One control forces the TAP reporter (`# tests 15`, the form Node 22 prints without a TTY), so the 2026-10-23 parser fix is tested on every Node version. | `20261026-host-controls/` |
| H-03 | `tests/unit/install-test.py` | Pass, 2026-10-26 | `20261026-host-controls/` |
| H-04 | `tests/unit/test_build_paths.py`: script and manifest paths, `series` files | Pass, 3 tests, 2026-10-26 | `20261026-host-controls/` |

## Not covered

More than 2 vCPUs, repeated runs for variance, a real T7610 TUI latency comparison per CPU
profile. See [KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md).
