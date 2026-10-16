# T7610 KVM run of Haiku.5, CPU profiles and coding fixture

16 October 2026 (Australia/Melbourne). Persistent cardless Haiku hrev60207
VM from [KVM-VM.md](KVM-VM.md): `-accel kvm -cpu host`, 2 vCPU, 8 GiB, host Dell
Precision T7610 (2 x E5-2620 v2, no AVX2) shared with a running host LLM service
(host load about 1.3 during the run). Source commit staged: `d648a06`. No GPU,
host sudo, host driver or host LLM service was touched. Evidence is in
`results/t7610-20261016-haiku5/`. These are **CPU** results.

## Runtime used (rebuilt on this host, not the committed archive)

The Haiku.5 archive is not in Git, so it was rebuilt here with
`tools/tui-port/build_bundle.sh` (`host-build.log`). It is **not byte-identical**
to the archive recorded in HAIKU5-ACCEPTANCE.md:

| | This run | Recorded (TCG run) |
|---|---|---|
| Archive SHA-256 | `9cbd07c5ed9758f7e1182603a164945cdb94ecbf0b2282633da86e03b57fb4f1` | `b9970cd8592ad48050c9340579c6d3e4d3d7c326e7e603cb921afbea481cf8f2` |
| Bytes | 53,687,592 | 53,682,981 |
| Bundle | `2db5b1b1...` (same) | `2db5b1b1...` |
| Renderer (`libopentui.so`) | `908b0308...` | `d0eed90c...` |
| Haiku SDK input | `cab6ca55...` ("current") | `7ed6dec0...` ("previous documented build") |
| Koffi addon | `36b37419...` ("current") | `cd03766f...` ("previous documented build") |

The difference follows the SDK and addon inputs available on this host; both
variants are recorded in `reference/TUI-PORT-INPUTS.json`. The renderer was not
compared bit-for-bit across builds. The first build attempt failed at packaging
(`host-build-first-attempt-failed.log`): the pinned `opencode-pty` source tree
needed for its LICENSE was not extracted; extracting `cache/opencode-pty-0.2.0.tar.gz`
fixed it. The tracked `results/opencode-tui-package.json` and
`results/native-build-inputs.json` were left as committed; this run's versions are
`package-rebuilt-on-kvm-host.json` and `native-build-inputs-rebuilt.json`.

## Results

| Check | Result | Evidence |
|---|---|---|
| Install, checksum, `selftest.cjs` | Pass: `SELFTEST_PASS` | `install.log`, `selftest.log` |
| Native daemon suite (`pty.sh`) | Exit 0. 30+5+6+3+1+9 = 54 tests, formatting, Clippy, `PTY-DONE` | `pty-full.log`, `pty-exit.log` |
| API probes (`api.sh`) | Exit 0: file/shell/session, legacy PTY, persistent terminal (UTF-8, resize, replay, exit 5) | `api-full.log` |
| llama.cpp baseline and Ivy Bridge builds | Both `CPU_PROFILE_PASS`; AVX/F16C/SSE4.2 usable in guest | `cpu-builds.log` (hashes, platform) |
| Benchmark, 3 repetitions | Table below | `bench-3rep.log` |
| Direct inference, Ivy Bridge 512/128 | HTTP 200 x3; outputs `OK`, add function, `12` (same as earlier recorded) | `profile-inference.log`, `jobinf-haiku5-profile.json` |
| 8-step coding fixture | `semantic_pass` true: agent ran `node test.mjs`, test unchanged, independent run passed; about 5 min, no deadline | `coding-job.log`, `coding-native-*` |
| TUI terminal pane | Opens (no crash), shell I/O, UTF-8 (`PANE_OK é€`), child `exit 3` closes pane | `screens/tui-*.png` |
| TUI clipboard paste | Alt-V inserted the exact marker into the prompt; not submitted; clipboard cleared after | `clipboard-set.log`, `screens/tui-clipboard-paste.png` |
| TUI exit / cleanup | Exits to shell; terminal list `[]` | `tui-cleanup.log`, `screens/tui-exit.png` |

### Benchmark (`llama-bench`, Qwen3 1.7B Q4_K_M, `-t 2`, 512-token prompt, 64-token decode, tokens/s, mean (sd) of 3)

| | Baseline (SSE2) | Ivy Bridge (SSE4.2+AVX+F16C) |
|---|---|---|
| Prompt, batch 128/32 | 0.74 (0.10) | 2.10 (0.36) |
| Prompt, batch 512/128 | 0.83 (0.07) | 11.00 (0.06) |
| Decode, batch 128/32 | 1.09 (0.00) | 6.66 (0.01) |
| Decode, batch 512/128 | 0.24 (0.12) | 6.72 (0.01) |

`bench-3rep.log` also contains the earlier 1-repetition smoke JSON (first eight
entries). Baseline decode at 512/128 is consistently low (0.37, 0.16, 0.18); the
cause is not established. The benchmark is synthetic throughput, not OpenCode
latency, and says nothing about the K40c.

## Not done or not established

- **WebPositive terminal panel** and pairing were not tested on the KVM VM. The
  TCG run in HAIKU5-ACCEPTANCE.md covers them for that archive.
- TUI **resize and session reconnect** were not repeated visually here; the
  persistent terminal API probe (resize, replay, reconnect, exit) passed.
- Only one coding run; passing it is not a reliability measure.
- A full OpenCode TUI **latency** comparison between profiles was not made. The
  earlier 15m51s first exchange (baseline) is not reproduced or retested.
- The renderer difference from the recorded archive was not investigated.
- Intermediate failure of mine: typing a leading `.` into the guest terminal was
  dropped, so the first TUI launch had no password; relaunched with `source`.

## Operational notes

- The guest job agent processes `jobN.sh` strictly in order; never skip numbers.
  A monitor that polled with high numbers blocked it until the agent was
  restarted at a fresh number.
- `api.sh` and the coding workflow upload to names that overwrite tracked
  `results/` files (`final-api-probe.*`, `legacy-api-probe.*`, `native-coding-*`,
  `native-agent-model.log`). They were restored with `git checkout`; this run's
  copies are in the dated directory. Use distinct upload names next time.
- VM left shut down cleanly (`qemu-img check`: no errors); transfer service stopped.
