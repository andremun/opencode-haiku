# Development and test setup

Split from `T7610-HAIKU-SETUP.md` on 23 October 2026. Section numbers are those of that guide. "Section N" refers to them: sections 1 to 7, 11 and 12 are in [DEVELOP.md](DEVELOP.md), sections 8 and 9 in [INSTALL.md](INSTALL.md), section 10 in [BUILD.md](BUILD.md).

The llama.cpp sections (4 to 7) describe a local model endpoint for tests. The patched llama.cpp source comes from the `haiku-k40c-llm` repository (section 4). The VM tools are in `haiku-k40c` (decision D4).

Prepared 15 October 2026. Commands labelled **Haiku** run in the guest;
commands labelled **Linux build host** run in the OpenCode repository on Linux.
Use a cardless VM throughout. No host sudo, GPU passthrough, CUDA installation,
or changes to existing host model services are required.

## 1. What is tested, and what this guide enables

The tested application stack is native x86_64 Haiku hrev60207, Node 24.21.0-1,
patched llama.cpp b8861, Qwen3 1.7B Q4_K_M, and OpenCode 2.0.29 with its full
OpenTUI interface and browser GUI. Text inference, cross-interface sessions,
file/shell operations, session persistence and native clipboard have passed.
The new persistent terminal daemon passes all 54 native upstream tests; the
separate Node PTY binding passes native I/O, resize and exit checks.

The current combined runtime is **2.0.29-haiku.5**. Its build, fresh native installation, API checks and visual TUI/browser
terminal controls pass on the local TCG VM. See [ACCEPTANCE.md](ACCEPTANCE.md). Earlier
Haiku.2/Haiku.3 GUI/TUI evidence does not establish those new terminal panels.
See [status](STATUS.md) and [continuation results](history/20261015-continuation-outcome.md).

This guide provides two routes:

1. **Recommended for the T7610 experiment:** build llama.cpp natively, then
   install the existing verified OpenCode runtime archive. No Bun, Zig or Rust
   is needed to run that archive.
2. **Complete source rebuild:** use Linux for Bun/Zig builds, export a Haiku
   SDK, build the native bindings and Rust daemon in Haiku, and package the
   resulting OpenCode runtime. Building the whole upstream application with
   Bun directly in Haiku is not the tested route.

The patched llama.cpp source for the local model endpoint comes from the
`haiku-k40c-llm` repository (section 4). The OpenCode patches are in
`patches/<component>/`.
Source archives, models, SDKs and generated runtime archives are ignored and
are not included by a Git clone. Transfer or regenerate them as described here.

## 2. VM requirements and hardware acceleration

Use an installed **x86_64 Haiku** guest, a persistent BFS disk and a graphical
console with Terminal and WebPositive. The tested system is hrev60207; another
nightly is a new platform combination and should have its revision recorded.
Start with **8 GiB RAM and 2 vCPUs** for a like-for-like run. A 32 GiB guest
disk is adequate for the runtime, model and llama build; use more space for
Rust builds and caches. These are starting allocations, not proven minima.

For a Linux/QEMU host, inspect without sudo:

```sh
ls -l /dev/kvm
test -r /dev/kvm && test -w /dev/kvm && echo KVM_ACCESS_OK
qemu-system-x86_64 -accel help
```

Start your existing cardless VM with `-accel kvm -cpu host` if it can use KVM.
Do not add those arguments to an already running VM. Preserve its disk and EFI
settings. An explicitly requested KVM accelerator should fail if unavailable;
do not count a silent fallback to TCG as an accelerated result. Query `info kvm`
in the QEMU monitor and save the actual launch command. `tools/haiku/app_vm.py` in the `haiku-k40c`
repository starts the persistent VM with `--kvm` and records the launch command (`docs/KVM-VM.md`).

For another hypervisor, record its hardware-virtualisation status and CPU
exposure settings. The present development host has no `/dev/kvm` and exposes
neither `vmx` nor `svm` to this environment. Enabling nested virtualisation there
requires an outer-host change; this guide performs no such change.

On the T7610, record the **actually installed CPUs**, not planned upgrades.
First compare the existing baseline build at 2 vCPUs. Later try 4/8 vCPUs and
an AVX-enabled llama build separately. An E5-2697 v2 supports AVX but not AVX2;
do not enable AVX2/FMA/BMI2 merely because the Linux build host supports them.
A changed CPU model, instruction set or thread count confounds a pure
TCG-versus-KVM comparison and must be identified in the results.

## 3. Transfer files and install guest packages

Clone or copy this repository to the Linux build machine and, for source
rebuilding, copy it to `/boot/home/opencode-haiku-src` inside Haiku. Substitute
your actual clone path; there is no public remote URL prescribed here.
Record `git rev-parse HEAD` and `git status --short`. Include uncommitted port
files when transferring the current working tree; a clone alone may omit them.

Use a shared folder, removable image, or an HTTP file server. A simple transfer
server on Linux is:

```sh
mkdir -p share
python3 -m http.server 18080 --bind 127.0.0.1 --directory share
```

In the tested QEMU user-network guest, `http://10.0.2.2:18080/` reaches the host.
That address is specific to this arrangement. On the T7610 use its shared-folder
facility or a reachable host address; bind an HTTP server to the appropriate
host interface only if that is necessary. This simple server supports downloads,
not uploads. Use the shared folder for exports or the repository's transfer
service with its documented arguments. Record hashes before and after transfer.

**Haiku, runtime and native llama build:**

```sh
pkgman install -y nodejs24 ripgrep cmd:g++ cmd:cmake cmd:make cmd:git cmd:patch
node --version
node -p 'process.platform + " " + process.arch'
g++ --version
cmake --version
uname -a
```

The expected Node platform/architecture is `haiku x64`; Node must be at least 24.
If a package provider is unavailable, inspect `pkgman search` rather than
substituting an incompatible Linux binary. Curl, tar, sha256sum and a working
network connection are also required for the download route.

**Only for a complete OpenCode native rebuild:**

```sh
pkgman install -y nodejs24_devel libffi_devel rust_bin
rustc --version --verbose
cargo --version
```

The daemon needs Rust >=1.90 / edition 2024. Native Rust 1.94.1-1 was installed
and tested; older HaikuPorts source recipes do not describe that installed
package. Native GCC 13.3 was used. Development headers for `libbsd` and the Be
API must be present for the PTY binding and clipboard helper; missing
`bsd/pty.h` or `Be.h` is a development-package problem, not a reason to remove
the associated code. Save the installed package/version list for reproduction.

## 4. Obtain and patch llama.cpp

The `haiku-k40c-llm` repository prepares the patched llama.cpp source. Its
inputs are pinned in its `reference/LLAMA-INPUTS.json`: base commit
`cf8b0dbda9ac0eac30ee33f87bc6702ead1c4664`, the `llm-server` patch set and
`reference/haiku-portability.patch`, each with a SHA-256.

**Linux build host** (in the `haiku-k40c-llm` checkout):

```sh
make bootstrap    # verified pinned archives, unpacked source
make prepare      # applies the patches, writes share/llama-haiku.tar.gz
make transfer     # file service for the guest on 127.0.0.1:18080
```

**Haiku:**

```sh
mkdir -p /boot/home/haiku-llm
cd /boot/home/haiku-llm
curl -fS -o llama-haiku.tar.gz http://10.0.2.2:18080/llama-haiku.tar.gz
tar -xzf llama-haiku.tar.gz       # creates llama/
```

The bundle is already patched. Do not apply the patches again. The current
`llm-server` patch set also contains `security-backports-b11393.patch`, which
the source recorded on 15 October 2026 did not have. The Kepler patch is in
the set, but CUDA is disabled and none of its GPU code is exercised.

## 5. Build and verify native CPU llama.cpp

**Haiku:**

```sh
cd /boot/home/haiku-llm
cmake -S llama -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_NATIVE=OFF -DGGML_SSE42=OFF \
  -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_BMI2=OFF \
  -DGGML_FMA=OFF -DGGML_F16C=OFF \
  -DGGML_CUDA=OFF -DGGML_OPENMP=OFF \
  -DLLAMA_OPENSSL=OFF -DLLAMA_BUILD_WEBUI=OFF -DLLAMA_BUILD_TESTS=ON
cmake --build build --parallel 2 --target \
  llama-cli llama-completion llama-server test-reasoning-budget test-chat-template
export LIBRARY_PATH=/boot/home/haiku-llm/build/bin:/boot/system/lib
./build/bin/test-reasoning-budget
./build/bin/test-chat-template
./build/bin/llama-server --version
```

Preserve build output and exit codes. Haiku uses `LIBRARY_PATH` for these shared
libraries. `LD_LIBRARY_PATH` was not the successful fix in the recorded run.
The baseline intentionally avoids extra CPU instructions for qemu64 compatibility.
For an accelerated CPU optimisation experiment, use a different build directory
and change only flags supported by the CPU exposed to Haiku. Preserve baseline.

**Adopted default (18 October 2026):** after the baseline build above, run
`sh build-cpu-profile.sh ivybridge` in the guest (the script is in the `haiku-k40c-llm` repository, `results/20261018-community-comparison/scripts/`) (SSE4.2, AVX, F16C, **OpenMP off**; it checks
that the guest CPU exposes them and refuses otherwise). `tests/acceptance/vm/services.sh` now starts this
build by default. Evidence on the KVM guest (E5-2620 v2, 2 vCPU): decode 6.7 tokens/s against 4.1 for
the production-matching build with OpenMP, and prompt throughput no different; the baseline is much
slower. Rationale and numbers: `docs/history/20261016-t7610-kvm-haiku5-results.md` and the 18 October
addendum in `docs/history/20261018-phase-1-3-results.md`. The SSE2 build stays available
(`OPENCODE_LLAMA_PROFILE=installed`). This default assumes a guest that exposes AVX and F16C; on a
different CPU re-check with `build-cpu-profile.sh` first.
Do not carry this global `LIBRARY_PATH` override into Cargo; see section 10.

## 6. Download and verify the model

Use the same small model for the first T7610 comparison. The production 35B
model is unnecessary for this experiment.

**Haiku, or Linux followed by file transfer:**

```sh
mkdir -p /boot/home/haiku-llm/models
cd /boot/home/haiku-llm/models
curl -fL --retry 3 --continue-at - \
  https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/dcb19155b962dbb6389f4691a982043a8e651022/Qwen_Qwen3-1.7B-Q4_K_M.gguf \
  -o Qwen3-1.7B-Q4_K_M.gguf
echo '72c5c3cb38fa32d5256e2fe30d03e7a64c6c79e668ad84057e3bd66e250b24fb  Qwen3-1.7B-Q4_K_M.gguf' | sha256sum -c
wc -c Qwen3-1.7B-Q4_K_M.gguf
```

Expected size: **1,282,439,584 bytes**. The model is a separate licensed input;
retain its publisher/model licence information when redistributing it. Do not
commit the weights to Git. A checksum failure must be resolved before inference.

## 7. Start llama-server and test it independently

**Haiku, its own Terminal:**

```sh
cd /boot/home/haiku-llm
export LIBRARY_PATH=/boot/home/haiku-llm/build/bin:/boot/system/lib
./build/bin/llama-server \
  -m models/Qwen3-1.7B-Q4_K_M.gguf \
  -ngl 0 -t 2 -tb 2 -b 128 -ub 32 -c 4096 \
  --parallel 1 --poll 0 --poll-batch 0 --cache-ram 128 \
  --host 127.0.0.1 --port 18081 --alias haiku-qwen17 \
  --reasoning off -n 128 > llama-server.log 2>&1
```

The process remains in that Terminal until Ctrl-C. Wait for loading to finish;
the emulated guest needed about 100 seconds in one cold load. In another Terminal:

```sh
curl -fS http://127.0.0.1:18081/health
curl -fS http://127.0.0.1:18081/v1/models
curl -fS --max-time 1800 http://127.0.0.1:18081/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"haiku-qwen17","messages":[{"role":"user","content":"Reply with OK only."}],"temperature":0,"seed":1234,"max_tokens":64,"stream":false,"chat_template_kwargs":{"enable_thinking":false}}' \
  -o inference-ok.json
```

Confirm a successful HTTP response and generated content before debugging
OpenCode. Keep one model request active at a time during the comparison.
Do not start a second model server on the same port. Capture llama.cpp timing
fields and server logs, not only wall-clock duration.

## 11. T7610 acceptance and speed comparison

Run sequentially, with compilation and other inference jobs stopped:

1. Record guest revision, package versions, actual CPU model/features, RAM,
   vCPUs, hypervisor acceleration and launch configuration.
2. Record repository commit/dirty state, source/patch hashes, native binary
   hashes, model checksum and complete model-server command.
3. Pass native llama tests and model health; pass the OpenCode self-test.
4. Submit the same three fresh inference controls: OK-only; Python `add(a,b)`
   returning their sum, code only; `7 + 5`, number only. Use the same request
   bodies as `results/20261015-terminals-clipboard/inference-compare-haiku.json` and seed 1234.
5. Repeat with fixed prompts after restarting the model for a cold comparison,
   then record a warm run separately. Save prompt/decode timings, generated
   token count and wall time. Earlier Linux/Haiku controls had different cache
   states and are functional controls, not a clean acceleration benchmark.
6. Pass TUI prompt/response, clean exit, session restore, GUI pairing, and
   shared-session live updates. Test Haiku text clipboard paste separately.
7. Test terminal panels separately through the combined runtime: command I/O,
   UTF-8, resize, child exit, reconnect and cleanup. These controls now pass locally in Haiku.5; repeat them on the T7610.
8. Attempt a disposable coding fixture: read a broken add function, change it,
   run its immutable test, record all tool calls and outcomes. Use a fixed
   deadline and retain the unchanged fixture if no edits occur. The TCG attempt
   reached 45 minutes during prompt processing; that is a resource/time limit,
   not an observed wrong patch. Small-model quality remains a separate question.
9. After the baseline, vary thread count and CPU optimisation one at a time.
   Do not promise a speedup from the hardware specifications alone.

Store evidence under a new result directory with a date and platform label.
Keep secrets out of logs. A direct speed ratio is meaningful only with matched
source, model, workload and cache state; a T7610-versus-development-host result
also changes physical hardware, so label it as a platform comparison.

## 12. Troubleshooting and shutdown

| Symptom | Check/action |
|---|---|
| Missing libllama/libggml | Add the native build/bin directory to Haiku LIBRARY_PATH for llama processes |
| Cargo cannot locate librustc_driver | Unset the manual LIBRARY_PATH override before running Cargo |
| Illegal instruction in addon | Clean and rebuild patched Koffi for baseline x86-64; confirm guest CPU exposure |
| fs.watch ENOSYS | Run the provided launcher so the polling fallback is loaded |
| Five-minute fetch failure | Use the packaged Haiku HTTP fallback and explicit provider timeouts |
| SQLite locking protocol | Stop duplicate backends; use one profile owner and attach clients to it |
| Model endpoint fails | Verify llama health directly before debugging the OpenCode provider |
| GUI authentication failure | Issue a fresh one-time code on the same running backend |
| Severe guest memory pressure | Stop concurrent builds/model requests; increase RAM before a clean rerun |
| Embedded terminal failure | Test daemon and Node PTY independently, then bundle integration; do not assume baseline GUI evidence covers terminals |

Exit TUI, stop OpenCode backend with Ctrl-C, then stop the model Terminal with
Ctrl-C. Shut Haiku down cleanly before snapshotting/copying its disk. Do not
kill an unrelated host model service or reset a GPU. Native clipboard images,
primary selection and recursive watching are not implemented. Browser GUI
support does not imply a native Electron desktop port. These are CPU results
and make no claim about K40c compute support.

For a concise manual pull/build/stage workflow and new CPU/coding experiments,
read [T7610-NEXT-RUN.md](history/20261015-t7610-next-run.md).
