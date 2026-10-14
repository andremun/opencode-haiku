# Status

Updated 15 October 2026. Independent repository:
`/home/unimelb.edu.au/mariom1/Documents/packages/opencode-haiku`.

The acceptance workflow now runs: **full upstream OpenCode TUI and browser GUI
in Haiku, connected to native Haiku llama.cpp CPU inference**. This is the full
OpenTUI interface, rather than the upstream mini/headless interface.

OpenCode 2.0.29 is pinned at `34d8ded0c58dd66808c1d60e081e8c66da12a896`;
current port build is `2.0.29-haiku.2`. Bun 1.4.2 builds the Node bundle.
Native Haiku uses Node 24.21.0-1, OpenTUI 0.5.17 and patched Koffi 3.3.3.
The native renderer uses Zig 0.16.0 and an exported Haiku SDK. Exact source,
patch, SDK, model and output hashes are recorded under `reference/` and
`results/opencode-tui-package.json`.

## Accepted evidence

- Qwen3 1.7B Q4_K_M downloaded and checksum-verified against the publisher.
- Native Haiku llama-server returns OK through its OpenAI-compatible API.
- Full TUI renders, accepts a prompt and displays native CPU model output.
  The first exchange took 15m41s in the 2-vCPU/4-GiB QEMU TCG guest.
- Clean TUI Ctrl-C exit returns 0. `--continue` restores the saved conversation.
- Native WebPositive renders the upstream GUI, authenticates through a one-time
  pairing link, opens the TUI-created session and submits a follow-up prompt.
- GUI-submitted follow-up appears live in the resumed TUI. Its model response
  appears in the GUI. The model returned OK instead of the requested Python
  function: recorded as poor coding quality, not an acceptance failure under
  the user's instruction. General coding usefulness is not established.
- Native FFI widths, BigInt, shared buffers, callbacks, callback release and
  closed-library rejection pass. The final archive's native FFI test passes
  with piped stdout and clean exit 0.
- Upstream OpenTUI FFI suite: 23 tests / 90 assertions pass.
- Polling watcher create/modify/delete/close/abort tests pass on Linux and Haiku.
- Pthread futex publication/wake races (200 rounds) and timeout tests pass on
  Linux and Haiku; waits use monotonic deadlines.
- Private server with its own database reports readiness and exits 0 when its
  stdin ownership lease closes. Use one backend per Haiku SQLite state profile.
- Self-contained runtime archive includes the guest-built FFI addon; fresh
  extraction passes checksum and native version checks. The full TUI
  starts from that extraction and restores both recorded exchanges.

## Port corrections and unsuccessful attempts

- CNoke initially selected x86-64-v2 and crashed on SSE4.1 under qemu64. The
  patch selects baseline x86-64 on Haiku and preserves other platforms.
- Native Node fs.watch returns ENOSYS. A bounded, nonrecursive polling fallback
  handles real configuration/model-preference/plugin/storage changes.
- Zig's Haiku I/O branch required error-set, positioned-I/O, socket-mode,
  threading and futex corrections. In-process Zig debug symbolisation remains
  explicitly unavailable; raw addresses/native Debugger remain available.
- The first model request hit the default five-minute response-header timeout.
  The VM test provider allows 30 minutes. This was an environment timeout.
- A manual-password GUI connection failed. Same-origin authenticated fetch/XHR
  controls both returned HTTP 200; the supported one-time pairing flow passed.
- A second server opening an already-owned SQLite profile failed with locking
  protocol. Its failed shutdown exposed an addon fsync error on piped stdout;
  the Haiku patch skips durability sync for valid nonregular streams. The final
  archive's piped native test exits cleanly. Raw crash reports stay outside Git,
  with hashes and diagnosis recorded in `reference/CRASH-PROVENANCE.json`.
- Overlapping preliminary model checks contaminated one response/log. The
  uncontended native-clean JSON and visual TUI/GUI evidence are accepted.
- Free-model access previously returned HTTP 403 from the port and official
  Linux release. No paid service or identity spoofing was used.
- Automatic approval review rejected guest SSH with root login. No SSH daemon
  was started; all VM work uses console controls and localhost transfers.

## Limits

Persistent PTY, recursive filesystem watching and native OS clipboard integration
remain unsupported. Ordinary file and shell tools were validated in the earlier
headless phase; the new GUI/TUI model checks use a restricted synthetic fixture.
The browser GUI is supported here; a native desktop/Electron port is not claimed.
WebPositive showed a cosmetic black session-tab label in the tested view.
This cardless CPU result is not evidence of K40c compute support.

## Resources

The independent cardless VM remains running. Native llama-server listens on guest
127.0.0.1:18081; the shared OpenCode API/GUI backend uses guest 127.0.0.1:18083.
The host transfer service is bound to localhost:18080. The verified temporary guest-only
browser diagnostic on port 18084 was stopped after verification.
Original project VM and former host CPU model server/relay remain stopped.
No physical GPU, host driver, host sudo or existing host LLM service was used.

See [the acceptance report](TUI-ACCEPTANCE.md),
[earlier headless evidence](OPENCODE-HAIKU-PORT.md), and
`reference/REPOSITORY-SPLIT.json`.
