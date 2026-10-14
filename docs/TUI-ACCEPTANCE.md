# Native Haiku OpenCode acceptance

Updated 15 October 2026.

**The tested workflow works:** the full upstream OpenCode TUI and browser GUI
run in Haiku and use native Haiku llama.cpp CPU inference. This uses OpenTUI,
not the upstream mini interface. It establishes application portability and
CPU inference; it does not establish K40c compute support.

## Acceptance evidence

| Check | Outcome | Evidence |
|---|---|---|
| Stronger small model | Qwen3 1.7B Q4_K_M downloaded; publisher SHA256 verified | `reference/TUI-MODEL.json` |
| Native CPU endpoint | Native Haiku llama-server returns OK | `results/opencode-tui-native-clean.json` |
| Full TUI conversation | Prompt entered; native model response displayed | `results/tui-native-model-response.png` |
| Clean TUI exit | Ctrl-C returns 0 | `results/opencode-tui-clean-exit.log` |
| Session recovery | `--continue` restores both exchanges | `results/tui-final-package-restored.png` |
| Native browser GUI | WebPositive authenticates using one-time pairing; opens the TUI-created session | `results/gui-native-restored-session.png` |
| GUI model exchange | Follow-up submitted in GUI; native response displayed | `results/gui-native-model-response.png` |
| Live shared session | GUI follow-up appears in resumed TUI | `results/tui-native-session-recovery.png` |
| Packaged native runtime | Fresh archive checksum/version checks; its own bundled addon passes native FFI and piped shutdown, exit 0 | `results/opencode-final-deploy.log`, `results/opencode-final-runtime.log` |
| FFI regression | Signed widths, BigInt, shared/sliced buffers, callbacks, release and closed-library rejection pass | `results/opencode-final-runtime.log` |
| Upstream FFI suite | 23 tests, 90 assertions pass | `results/opentui-ffi-regression.log` |
| Configuration watching | Create, modify, delete, close, abort and recursive rejection pass on host and Haiku | `results/watch-host-test.log`, `results/opencode-watch-native.log` |
| Synchronization | 200 publication/wake races and bounded timeout pass on host and Haiku | `results/futex-host-test.log`, `results/opencode-futex-native.log` |
| Private server lifecycle | Own database: readiness reported; stdin lease closure exits 0 | `results/opencode-standalone-private-state.log` |
| Native rebuild wrapper | Patched renderer rebuild passes | `results/opentui-final-rebuild.log` |

The first full TUI exchange took **15 minutes 41 seconds** under QEMU TCG with
2 virtual CPUs and 4 GiB RAM. This is emulation performance, not a native-machine
benchmark. The GUI follow-up took approximately three minutes.

The coding prompt asked for a Python `add(a, b)` function. The model answered
`OK`, so coding quality was poor in this test. As requested, that is an
observation, not an acceptance failure. The UI/server/model path remains real;
this test does not establish useful autonomous coding. These conversation tests
use a restricted synthetic fixture. Native file/shell operations and permission
handling were verified in the earlier headless phase.

## Runtime and model

- OpenCode 2.0.29: `34d8ded0c58dd66808c1d60e081e8c66da12a896`.
- Port label: `2.0.29-haiku.2`; native Node 24.21.0-1.
- OpenTUI 0.5.17: `6f0efd3330978d696b42db3d7d95d2042008312b`.
- Zig 0.16.0; Koffi 3.3.3; Haiku hrev60207 x86_64.
- Qwen3 1.7B Q4_K_M: 1,282,439,584 bytes, SHA256
  `72c5c3cb38fa32d5256e2fe30d03e7a64c6c79e668ad84057e3bd66e250b24fb`.
- Native model URL: guest `http://127.0.0.1:18081/v1`, alias `haiku-qwen17`.
- Shared OpenCode backend: guest `http://127.0.0.1:18083`.

The runtime archive is in ignored `share/` and includes the native renderer,
Node bundle, browser assets, FFI facade, polling watcher and guest-built Koffi
addon with its runtime JavaScript and licenses. Its exact checksum is recorded
in `results/opencode-tui-package.json`. Installation does not require building
Koffi or linking to a build checkout. Node remains an installed guest dependency;
the model and llama-server are separately selected services.

## Reproduction

The cached-source build is automated by `tools/tui-port/build_bundle.sh`; it
rebuilds the native renderer and JavaScript, installs the patched dependency,
runs upstream artifact verification, and packages the runtime.

Sources, SDKs, toolchains, models, virtual disks and binaries remain outside Git.
`reference/TUI-PORT-INPUTS.json` records their exact hashes and the final patches.

1. Use the independent cardless VM via `tools/app_vm.py`. Never add GPU devices
   or host-sudo steps. Install native Node/development dependencies as recorded
   by `environment_guest.sh` and `setup_guest.sh` in `tools/tui-port/`.
2. Export the guest SDK using the setup/build scripts. Run
   `tools/tui-port/build_native.sh`; it verifies archive/SDK hashes and applies
   the Zig/OpenTUI patches before the renderer build.
3. Apply `reference/koffi-portability.patch` to the pinned Koffi source. Package
   it in ignored share and run `build_ffi_guest.sh` in Haiku. Its clean step
   prevents cached x86-64-v2 objects surviving the CPU-baseline correction.
4. Build OpenTUI `packages/core` with the pinned Bun:
   `bun scripts/build.ts --lib`. Install its dist into the pinned OpenCode
   dependency directory. Build OpenCode from its root with:
   `OPENCODE_VERSION=2.0.29-haiku.2 OPENCODE_CHANNEL=haiku bun packages/cli/script/build-node.ts --bundle-only --skip-install`.
5. Export the guest-built addon to ignored cache, then run
   `python3 tools/tui-port/package.py`. It validates the addon exists, packages
   through a temporary archive, and records output hashes.
6. Run `deploy_guest.sh` from `tools/tui-port/` using the recorded archive hash.
   It extracts a self-contained `final-port` directory in the guest.
7. Start the separately installed native CPU llama-server with
   `check_model_guest.sh`. Use `opencode.json` from the test tooling for the
   native endpoint; it deliberately restricts tools and raises VM header
   timeout to 30 minutes. Adapt permissions for a real coding workspace.
8. Start one OpenCode backend with `run_gui_guest.sh`, attach the TUI using
   `run_tui_guest.sh`, and use `--continue` to restore its session. Browser
   one-time pairing is the verified authentication path. Keep ephemeral
   passwords/pairing codes outside Git.

The standalone/private-server probe uses its own XDG profile. **Use one server
per Haiku SQLite state profile**; TUI and GUI should share that backend. Starting
another server against an already-owned profile produced a locking-protocol
error in the recorded test.

## Engineering corrections

The initial addon fault was an SSE4.1 `pinsrq` instruction during initialisation.
CNoke silently selected x86-64-v2; qemu64 lacked that instruction. The patch
selects baseline x86-64 only on Haiku. It also ports executable discovery,
thread naming and a GCC/N-API conversion. Valid nonregular streams avoid Haiku's
unsupported durability sync; the final piped native FFI test exits cleanly.

Zig's Haiku I/O implementation needed error-set, positioned-I/O/iovec,
socket-mode, threading and futex corrections. The process-private pthread
fallback uses hashed condition variables, permitted spurious wakes, monotonic
deadlines and bounded cancellation checks. `pwrite` implements a valid short
write where `pwritev` is unavailable. Unsupported in-process ELF debug discovery
returns missing-debug-info explicitly rather than inventing metadata.

Haiku Node does not implement `fs.watch`. The launcher installs real, bounded
polling for nonrecursive configuration directories, preserving filenames,
change/rename events, close/ref/unref and abort semantics. Recursive requests
fail explicitly. Addon loading is lazy at the facade boundary.

Unsuccessful attempts remain recorded: CPU-baseline crash, compiler portability
errors, checks attempted before a rebuild finished, initial five-minute model
timeout, manual-password GUI failure and contaminated overlapping preliminary
model output. Raw crash-memory reports are ignored; hashed provenance and
accepted replacement evidence are retained. Guest SSH was rejected by automatic
approval review because it enabled root login; no daemon was started and console
controls completed the work.

## Scope limits

Persistent PTY, recursive watching and native OS clipboard integration remain
unsupported. The browser GUI is tested; a native desktop/Electron port is not
claimed. WebPositive displayed a cosmetic black session-tab label. General
coding usefulness, every optional GUI feature and performance on native hardware
remain unestablished. No physical GPU, host driver, host sudo or existing host
LLM service was used.
