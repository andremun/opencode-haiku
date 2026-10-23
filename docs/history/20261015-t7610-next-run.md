# Manual T7610 continuation: Haiku.5 and CPU comparisons

15 October 2026. The T7610 is accessed manually, not over SSH. Pull committed
changes there; runtime archives and native build caches remain outside Git.
No GPU, host sudo, host driver change or existing host LLM service is needed.
All commands below that touch `/boot/home` run **inside the cardless Haiku VM**.

## 1. Linux host: pull, rebuild and stage

From the existing T7610 `opencode-haiku` clone:

```sh
git pull --ff-only
mkdir -p logs share
sh tools/tui-port/build_bundle.sh > logs/haiku5-build.log 2>&1
python3 tools/stage_t7610.py
python3 tools/transfer_server.py
```

The last command stays running in its own host terminal. Do not start a second
transfer service if port 18080 is already owned. The build now applies the
Ghostty VT renderer patch automatically and creates **Haiku.5**, preserving the
old Haiku.4 archive. It accepts only the current or explicitly recorded previous
SDK/addon checksums, and writes the exact selected inputs to
`results/native-build-inputs.json` and the output manifest. A new SDK or binary
requires its own recorded provenance, not removal of a checksum check.

`stage_t7610.py` verifies the runtime checksum and creates a Git archive of
**HEAD**, plus a generated checksum-aware guest deployment script. Commit code
before staging. Ignored upstream sources, models, SDKs and native binaries are
not in this source archive: the T7610's existing build inputs are still needed.
Follow T7610-HAIKU-SETUP.md if those inputs are missing.

## 2. Haiku console: update source and install

Boot the existing cardless VM with `python3 tools/app_vm.py start --installed
--kvm` on its host if it is stopped. Inside Haiku Terminal:

```sh
curl -fsS http://10.0.2.2:18080/next-step.sh -o /tmp/next
sh /tmp/next
```

This installs committed repository files under `/boot/home/opencode-haiku-src`
and the newly built runtime under
`/boot/home/opencode-haiku-2.0.29-haiku.5`. It refuses an existing installation;
for a rerun, choose a fresh destination with `OPENCODE_INSTALL_DEST` and use that
path in later commands. Never overwrite the old runtime as part of this test.

Run the native self-test, retaining exit status:

```sh
OC=/boot/home/opencode-haiku-2.0.29-haiku.5
export OPENCODE_HAIKU_KOFFI="$OC/koffi"
export NODE_OPTIONS="--require=$OC/haiku-loader.cjs"
export LIBRARY_PATH=/boot/system/lib
node "$OC/selftest.cjs"
unset NODE_OPTIONS OPENCODE_HAIKU_KOFFI
```

## 3. Native terminal verification with full logs

Run sequentially, with other guest builds/inference stopped:

```sh
SRC=/boot/home/opencode-haiku-src
sh "$SRC/tools/kvm-run/pty.sh" > /boot/home/haiku5-pty-full.log 2>&1
rc=$?
printf 'PTY exit=%s\n' "$rc"
```

Read the complete log. Expect 30 + 5 + 6 + 3 + 1 + 9 tests, plus formatting and
Clippy success, and final `PTY-DONE`. Do not pipe verification commands into
`tail` before capturing their status. This rerun closes the T7610 capture gap;
the new local TCG full-suite result alone does not do that.

The existing T7610 source directory defaults to `/boot/home/native-build/pty`.
For another layout set `OPENCODE_NATIVE_WORK` and `OPENCODE_PTY_SOURCE` explicitly.

```sh
OPENCODE_PORT_ROOT=/boot/home/opencode-haiku-2.0.29-haiku.5 \
 OPENCODE_ACCEPTANCE_WORK=/boot/home/haiku5-api \
 sh "$SRC/tools/kvm-run/api.sh" > /boot/home/haiku5-api-full.log 2>&1
rc=$?
printf 'API exit=%s\n' "$rc"
```

The source staging helper also serves the three API probes required by this
runner. Expect all probes to succeed, including persistent terminal replay,
UTF-8, resize and exit. These APIs do not invoke the LLM.

## 4. CPU variants and batch sizes

Do this before starting the model/OpenCode services. The following builds are
**new native Haiku binaries**, in separate directories; they preserve the
installed baseline and require the pinned llama source archive and all three
patches. The Ivy Bridge profile checks usable AVX/F16C/SSE4.2 in the guest and
refuses unsupported CPUs. AVX2, FMA and BMI2 remain off.

```sh
sh "$SRC/tools/kvm-run/build-cpu-profile.sh" baseline \
 > /boot/home/cpu-baseline-build.log 2>&1
sh "$SRC/tools/kvm-run/build-cpu-profile.sh" ivybridge \
 > /boot/home/cpu-ivybridge-build.log 2>&1
```

Verify both exit 0 and contain `CPU_PROFILE_PASS`. The builds run sampler and
chat-template tests and record binary/compiler-command hashes. If the Ivy Bridge
feature check fails, record the guest CPU exposure and stop that variant.

```sh
OPENCODE_BENCH_REPS=1 sh "$SRC/tools/kvm-run/benchmark-cpu.sh"
```

This smoke matrix runs both builds with batches **128/32** and **512/128**, two
threads, a 512-token synthetic prefill and 64-token decode. If it completes:

```sh
OPENCODE_BENCH_REPS=3 sh "$SRC/tools/kvm-run/benchmark-cpu.sh"
```

Results go under `/boot/home/haiku-llm/cpu-benchmark-TIMESTAMP/`, with command
lines, hashes, JSON timings and stderr. It could take considerable time at the
old baseline speed. Keep one-repetition smoke results separate from repeated
measurements. Compare prompt and decode throughput separately, including
variation; this synthetic benchmark is not an OpenCode latency measurement.
Record host CPU/load and guest allocation. Do not alter an existing host LLM
service to make a benchmark quieter.

## 5. Packaged UI and coding workflow

Choose the native profile and batches explicitly when starting owned **guest**
services. Example, after the baseline and matrix results have been saved:

```sh
OPENCODE_PORT_ROOT=/boot/home/opencode-haiku-2.0.29-haiku.5 \
 OPENCODE_LLAMA_PROFILE=ivybridge \
 OPENCODE_LLAMA_BATCH=512 OPENCODE_LLAMA_UBATCH=128 \
 sh "$SRC/tools/kvm-run/services.sh"
```

Use `installed` for the old binary or `baseline` for the newly built baseline.
The runner preserves existing credentials/configuration, refuses duplicate HTTP
listeners and verifies readiness. Stop your owned guest processes cleanly before
changing profile. It does not stop existing services automatically.

In another Terminal:

```sh
. /boot/home/opencode-env.sh
cd /boot/home/opencode-work
/boot/home/opencode-haiku-2.0.29-haiku.5/opencode \
 --server http://127.0.0.1:18083
```

Open a saved session. Ctrl-X then T opens its persistent terminal pane. Test
commands, UTF-8, resizing, TUI exit/reconnect, child exit and cleanup. The terminal
shortcut is session-specific; it does not open a pane from an empty home screen.
Pair WebPositive using `tools/kvm-run/pair.sh`, open the same session, and test
its separate browser terminal panel. Also paste native text into the TUI prompt
without submitting it as an inference request.

For coding, the runner now defaults to **eight steps**, a fresh private fixture
and profile per run, and keeps the immutable test's hash. Start it directly from
the updated repository, with the desired runtime path:

```sh
mkdir -p /boot/home/haiku5-coding
OPENCODE_TEST_PORT_ROOT=/boot/home/opencode-haiku-2.0.29-haiku.5/opencode \
 OPENCODE_TEST_STEPS=8 \
 node "$SRC/tools/tui-port/coding-workflow.mjs" /boot/home/haiku5-coding \
 > /boot/home/haiku5-coding/run.log 2>&1
```

The 45-minute deadline remains. `semantic_pass` requires the agent to run
`node test.mjs` successfully, an unchanged test, and a successful independent
run of that test. `independent_test_pass` records code correctness separately
when the model omits its shell call. Timeout/resource limits remain distinct
from observed coding mistakes. This is a new experiment, not a claimed success.

## 6. Return evidence

Save full logs, exit codes, the build/package/input manifests and screenshots
under a new dated `results/t7610-.../` directory in the host clone. Do not include
passwords, pairing codes, models, source caches or disks. Use the reviewed guest
job agent/transfer service or a shared folder to move logs; SSH is not required.
Update STATUS.md and commit the results for review. Native CPU results make no
claim about K40c compute support.

Before the coding run, also repeat the three direct functional requests against
the chosen CPU profile, keeping the response JSON:

```sh
node "$SRC/tools/tui-port/inference-compare.cjs" http://127.0.0.1:18081 \
 /boot/home/haiku5-profile-inference.json haiku5-profile-inference.json
```

HTTP/malformed response errors return failure; output correctness must also be
checked against the recorded requests. Do not infer numerical correctness or
model quality from llama-bench throughput alone.
