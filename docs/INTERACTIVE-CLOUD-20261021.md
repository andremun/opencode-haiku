# Interactive use with a cloud model: TUI, second client, browser (21 October 2026)

Guest times are UTC (02:39 to 03:05). Cardless KVM Haiku VM (`vm/system.qcow2`, hrev60207, 2 vCPU,
8 GiB), Haiku.5 port `2.0.29-haiku.5`, guest source `b66fa4f` plus `tools/kvm-run/cloud-serve.sh`
(SHA-256 `7f5a3751…`). No GPU, host service or host sudo. No push. Same no-credit key as the batch runs in
[TASK-E-20261021.md](TASK-E-20261021.md), served once to the guest (`serve-key-once.py` →
`with-cloud-key-guest.sh`) and held only in the backend's environment. Evidence:
`results/t7610-20261021-taskE/interactive/`.

## Setup

1. Guest `/boot/home/opencode-env.sh`: `OC=` changed from `…haiku.4` to `…haiku.5` (backup
   `opencode-env.sh.bak-20261021`). A bare `services.sh` now starts the current client.
2. `cloud-serve.sh /boot/home/cloud-interactive-20261021` starts one backend (`opencode serve`, 127.0.0.1:18083,
   private XDG state) on a fresh copy of the synthetic cloud task. It uses the same scoped permissions as the batch
   runner and records the test hashes.
3. Clients: TUI 1 and TUI 2 (`$OC/opencode --server http://127.0.0.1:18083`, the second with `--continue`) in
   separate Haiku Terminal windows. Browser: WebPositive opened on a pairing link from `pair.sh` (link
   not recorded; the guest files were removed afterwards).

## Results

| Check | Result |
|---|---|
| TUI 1: the CSV/report task, interactive | **Pass.** The agent read, edited and ran `node --test` (its own run: 15 pass, 0 fail) and replied DONE; 5 min 15 s for the turn. Independent check: tests unchanged, 15/15 (`tui1-task-done.png`) |
| TUI 2 attaches to the live session while TUI 1 stays open | **Pass.** Full history shown (`tui2-attached-history.png`) |
| Message from TUI 2 appears live in TUI 1 | **Pass** (MARKER_TWO, `tui2-marker.png`, `tui1-live-update.png`) |
| Message from TUI 1 appears live in TUI 2 | **Pass** (MARKER_ONE, `tui2-sees-marker-one.png`) |
| Browser (third client) opens the same session | **Pass.** History including both markers (`gui-session-history.png`) |
| Browser: real edit (add `version()` to `src/report.mjs`, run tests) | **Pass.** 2 edits plus a shell run, DONE (`gui-edit-done.png`). Independent check: `version()` returns `1.0.0`, tests unchanged, 15/15 |
| Browser turn appears in TUI 2 | **Pass** (`tui-sees-gui-turn.png`) |
| Clean exit | `/exit` in both TUIs (prints the `opencode -s <session>` hint); WebPositive quit; backend stopped by its PID; 18083 closed |

Model: `LongCat 2.5 Preview Free` from the account's Zen provider (shown as "Andrés / OpenCode"),
for every turn that ran. Final files: `interactive/fixture/src/`. The scoped permissions worked interactively: an
unlisted `node -e` command was denied and the agent continued without it.

## Usability findings

1. **The TUI ignored the project's `model`.** With `"model": "opencode/glm-5.3-flash-free"` in the project's
   `opencode.json`, the TUI started on **Claude Haiku 5.5 (OpenCode Go)**, a subscription model. Cause not
   established (client state, provider default or the config schema); the batch runner avoids it with
   `--model`. Interactive users should check the footer before the first prompt.
2. **The model list mixes free and subscription models.** The picker has two providers: "OpenCode Go" (subscription)
   and the Zen provider. The first selection by accident (`LongCat … OpenCode Go`) failed with "An active
   OpenCode Go subscription is required", which cost nothing. A search for `glm` puts the non-free
   `GLM-5.3-Flash` first; I left it without sending a prompt. The free Zen list in the picker (Exo, Ling 3.1
   Flash, LongCat, Space Bunny, MiMo) differs from today's public catalogue. Not examined further.
3. Small TUI redraw artefact on exit (leftover characters after the session hint). Known black browser
   session-tab styling persists.
4. Test-driver note, not a port issue: `tools/app_vm.py type` always presses Enter; use `write` to type
   into the picker without selecting.

## Interruption

At 13:50:50 local time the desktop app's Network Service was killed with signal 9 outside an app quit
(`~/.config/Claude/logs/main.log`), and the session ended with it. The host transfer service, a child of the
session, stopped. The VM, the backend and the guest job agent kept running; the transfer service was
restarted and the work continued from the same state. Free memory was about 34 GB, so the cause was not
memory pressure; the sender of the signal is not known.

## Key hygiene and end state

The key was fetched once by the guest. `scan_secrets.py`: no findings. A fixed-string search for the key
(through `with-cloud-key.sh`) over `results/t7610-20261021-taskE`, `logs/` and `share/` found nothing. The guest disk and
backend state were not searched for the key. VM shut down from inside Haiku; `qemu-img check`: no errors;
transfer service stopped. Guest job numbers used: 835 to 844.

## Not covered

Paid models; more than one cloud model interactively; the native rerun of the `coding-workflow.mjs` upload fix (the
local model was not started); anything about the K40c.
