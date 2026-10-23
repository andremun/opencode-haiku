# Known limitations

Limits of port `2.0.29-haiku.5` on Haiku hrev60207. Each row names the report that found it.

| Area | Limitation | Workaround | Found in |
|---|---|---|---|
| File watching | Recursive watching is not supported. The port polls. | None needed for normal use. | `history/20261015-haiku5-acceptance.md` |
| Clipboard | Images and the primary selection are not supported. Writing an empty stream through the helper fails. | Use text. Use the explicit clear operation. | same |
| Desktop app | No native Electron application. | Use the TUI or WebPositive. | same |
| Browser | Session tabs show black styling. The terminal panel can stay blank while its WASM renderer loads under TCG. | Wait, or open `/terminal`. | same |
| TUI | The terminal shortcut works only in a saved session, not on the empty home screen. | Create or open a session first. | same |
| TUI model choice | The TUI ignored the project `model` and started on a subscription model. The picker mixes free and subscription models. | Check the footer before you prompt. | `history/20261021-interactive-cloud.md` |
| Shared state | One backend for each Haiku SQLite profile. A second background service on the same profile is not supported. | Start one `opencode serve` and attach clients. | `INSTALL.md` |
| Cloud models | Free cloud models reject anonymous requests (HTTP 403). `jev-1.13-free` fails with `provider.no-route`. | Use a no-credit key ([SECRETS.md](SECRETS.md)). | `history/20261021-task-e.md` |
| Emulation | Input and start-up delays in emulated VMs. Not measured on real hardware. | None. | `history/20261015-haiku5-acceptance.md` |
| Autonomous coding | A local model passed the 8-step fixture, but reliable autonomous coding is not shown. | Review agent work. | `history/20261016-t7610-kvm-haiku5-results.md` |
| GPU | No GPU support. All model inference on Haiku is CPU-only. | Use a remote endpoint. | `README.md` |
