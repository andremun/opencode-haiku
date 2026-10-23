# T7610 KVM run of Haiku.5, CPU profiles and coding fixture

16 October 2026 (Australia/Melbourne). Persistent cardless Haiku hrev60207
VM from [KVM-VM.md](../KVM-VM.md): `-accel kvm -cpu host`, 2 vCPU, 8 GiB, host Dell
Precision T7610 (2 x E5-2620 v2, no AVX2) shared with a running host LLM service
(host load about 1.3 during the run). Source commit staged: `d648a06`. No GPU,
host sudo, host driver or host LLM service was touched. Evidence is in
`results/20261016-t7610-haiku5/`. These are **CPU** results.

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
| Direct inference, Ivy Bridge 512/128 | HTTP 200 x3; outputs `OK.`, add function, `12`. **Correction:** the first output is `OK.`, whereas the SSE2 installed build gave `OK` (see production section) | `profile-inference.log`, `jobinf-haiku5-profile.json` |
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

## Addendum 17 October 2026: production-matching build and the same without OpenMP

Request: verify, in this machine's VM, the CPU configuration of the host
`llm-server` llama.cpp (same source, commit `cf8b0dbd`, b8861), then repeat without
OpenMP. Evidence: `results/20261016-t7610-haiku5-production/`.

**Deployed configuration read (read-only):** `GGML_NATIVE=ON` (so `-march=native`),
`GGML_OPENMP=ON`, `GGML_LLAMAFILE=ON`, `GGML_CPU_REPACK=ON`, shared libraries,
CUDA on (arch 35), GCC 10.5. On this E5-2620 v2, `-march=native` resolves to
`ivybridge`: AVX, F16C, SSE4.2, AES, PCLMUL, POPCNT on; AVX2, FMA, BMI2 off.

**Profiles added** (`tools/kvm-run/build-cpu-profile.sh`, `benchmark-cpu.sh`, `services.sh`,
`prodrun.sh`): `production` = `GGML_NATIVE=ON`, `GGML_OPENMP=ON`; `production-noomp` = same
with OpenMP off. Both use CUDA off, OpenSSL and WebUI off (Haiku portability),
same pinned source and three patches as the earlier profiles. Differences from the
deployed build: no CUDA, GCC 13.3 (Haiku) instead of 10.5, no OpenSSL/WebUI.

**Verified in the guest** (`prod-builds.log`, `prod-link-and-march.log`):
both builds pass `test-reasoning-budget` and `test-chat-template`
(`CPU_PROFILE_PASS`); compile flags contain `-march=native` (and `-fopenmp` only in
`production`); guest `-march=native` resolves to `ivybridge` with the same enabled
and disabled flags as the host; `libggml-cpu.so` links `libgomp.so.1` (3 GOMP symbols)
only in `production`.

**Benchmark** (`llama-bench`, Qwen3 1.7B Q4_K_M, `-t 2`, 512-token prompt, 64-token
decode, 3 repetitions, tokens/s mean (sd); `bench-prod.log`; same session; the
Ivy Bridge profile is a control):

| Profile | Prompt 128/32 | Prompt 512/128 | Decode 128/32 | Decode 512/128 |
|---|---|---|---|---|
| ivybridge (explicit flags, no OpenMP) | 10.83 (0.11) | 10.07 (1.34) | 6.91 (0.03) | 6.75 (0.03) |
| production (native, OpenMP) | 9.95 (0.09) | 10.98 (0.02) | 4.10 (0.00) | 4.07 (0.02) |
| production-noomp (native, no OpenMP) | 10.77 (0.10) | 9.50 (2.94) | 6.69 (0.12) | 6.76 (0.04) |

**Direct inference and coding** (`run-production.log`, `run-production-noomp.log`,
`inference-both.log`; service batch 512/128, `-t 2`): every request HTTP 200 and
the same outputs (`OK.`, add function, `12`) for both. Both profiles pass the 8-step
coding fixture (`semantic_pass` true, test unchanged, independent test pass), in
about 4.5 min (`production`) and 4.2 min (`production-noomp`) including service
startup and inference. Direct decode speed from the requests: `production`
4.5-6.5 tokens/s; `production-noomp` 6.6-9.8 tokens/s.

**Findings**

- The production-matching CPU build works in the VM and matches the deployed
  instruction set, so the earlier explicit-flag Ivy Bridge profile is equivalent in
  CPU code; this validates the VM's build and test infrastructure against the host
  configuration (build, unit tests, benchmark, service, coding fixture).
- **OpenMP hurts decode here:** about 40% slower (4.1 vs 6.7-6.9 tokens/s) on the
  2-vCPU guest, with no prompt-throughput benefit. This is a result for this VM and
  model, not for the host's 6-thread GPU-offload service.
- **Corrects the earlier table:** the Ivy Bridge 128/32 prompt figure of 2.10
  (sd 0.36) and the baseline comparisons were taken in a different session; in this
  session the same profile gives 10.83. Prompt results vary between sessions and
  have at times a slow repetition (8.52 and 6.11 in the 512/128 cases), so treat
  prompt differences below about 15% as noise. Decode numbers are stable.
- The first inference output is `OK.` on all AVX builds but `OK` on the SSE2
  installed build: the instruction set changes floating-point results slightly.
  This was not investigated; the other two outputs are identical.

**Not done:** TUI/browser terminal checks were not repeated for these profiles;
the baseline was not re-run in this session; no measurement of the deployed host
binary (the host service was untouched). VM shut down cleanly, transfer service
stopped.
