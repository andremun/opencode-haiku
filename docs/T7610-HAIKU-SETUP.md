# Haiku llama.cpp and OpenCode: complete setup and T7610 test guide

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
terminal controls pass on the local TCG VM. See HAIKU5-ACCEPTANCE.md. Earlier
Haiku.2/Haiku.3 GUI/TUI evidence does not establish those new terminal panels.
See [status](STATUS.md) and [continuation results](CONTINUATION-OUTCOME.md).

This guide provides two routes:

1. **Recommended for the T7610 experiment:** build llama.cpp natively, then
   install the existing verified OpenCode runtime archive. No Bun, Zig or Rust
   is needed to run that archive.
2. **Complete source rebuild:** use Linux for Bun/Zig builds, export a Haiku
   SDK, build the native bindings and Rust daemon in Haiku, and package the
   resulting OpenCode runtime. Building the whole upstream application with
   Bun directly in Haiku is not the tested route.

The patch files needed for llama.cpp are preserved in this repository under
`reference/llama-cpu/`; the sibling LLM/server repositories are not needed.
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
in the QEMU monitor and save the actual launch command. `tools/app_vm.py` currently
controls the development TCG VM; it is not a ready-made KVM launcher.

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

You can perform this source preparation in either guest or build host. The
example assumes the repository is available in Haiku. Use a fresh directory:

```sh
mkdir -p /boot/home/haiku-llm
cd /boot/home/haiku-llm
curl -fL --retry 3 \
  https://codeload.github.com/ggml-org/llama.cpp/tar.gz/cf8b0dbda9ac0eac30ee33f87bc6702ead1c4664 \
  -o llama-source.tar.gz
echo '6980c77f4ad311bca845848f5b899d1a68b35dec94de849ca1b2ce4bc3ca0a3a  llama-source.tar.gz' | sha256sum -c
tar -xzf llama-source.tar.gz
mv llama.cpp-cf8b0dbda9ac0eac30ee33f87bc6702ead1c4664 llama
cd llama
PORT=/boot/home/opencode-haiku-src
git apply --check "$PORT/reference/llama-cpu/kepler-sm35-ggml-cuda.patch"
git apply "$PORT/reference/llama-cpu/kepler-sm35-ggml-cuda.patch"
git apply --check "$PORT/reference/llama-cpu/reasoning-budget-rearm.patch"
git apply "$PORT/reference/llama-cpu/reasoning-budget-rearm.patch"
git apply --check "$PORT/reference/llama-cpu/haiku-portability.patch"
git apply "$PORT/reference/llama-cpu/haiku-portability.patch"
```

These commands reproduce the recorded patched source. The Kepler patch is
included to match that source, but CUDA is disabled and none of its GPU code is
exercised. See `reference/llama-cpu/INPUTS.json` for patch hashes. Do not apply
these patches twice or to an arbitrary newer llama.cpp checkout.

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
`sh tools/kvm-run/build-cpu-profile.sh ivybridge` (SSE4.2, AVX, F16C, **OpenMP off**; it checks
that the guest CPU exposes them and refuses otherwise). `tools/kvm-run/services.sh` now starts this
build by default. Evidence on the KVM guest (E5-2620 v2, 2 vCPU): decode 6.7 tokens/s against 4.1 for
the production-matching build with OpenMP, and prompt throughput no different; the baseline is much
slower. Rationale and numbers: `docs/T7610-KVM-HAIKU5-RESULTS-20261016.md` and the 18 October
addendum in `docs/PHASE-1-3-RESULTS-20261018.md`. The SSE2 build stays available
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

## 8. Install OpenCode from the repository's prepared runtime

On Linux, locate `share/opencode-haiku-tui-2.0.29-haiku.5.tar.gz` and read
`results/opencode-tui-package.json`. Transfer the archive, the repository's
`tools/tui-port/install.sh`, and the example config below to Haiku.

The current archive is 53,682,981 bytes, SHA-256:
`b9970cd8592ad48050c9340579c6d3e4d3d7c326e7e603cb921afbea481cf8f2`.
After any rebuild, use the newly generated manifest rather than this snapshot.

**Haiku, from the directory containing the transferred files:**

```sh
sh install.sh opencode-haiku-tui-2.0.29-haiku.5.tar.gz \
  b9970cd8592ad48050c9340579c6d3e4d3d7c326e7e603cb921afbea481cf8f2 \
  /boot/home/opencode-haiku-2.0.29-haiku.5
OC=/boot/home/opencode-haiku-2.0.29-haiku.5
"$OC/opencode" --version
export OPENCODE_HAIKU_KOFFI="$OC/koffi"
export NODE_OPTIONS="--require=$OC/haiku-loader.cjs"
export LIBRARY_PATH=/boot/system/lib
node "$OC/selftest.cjs"
unset NODE_OPTIONS OPENCODE_HAIKU_KOFFI
```

Expected self-test: `SELFTEST_PASS: native FFI, watcher, clipboard read, clean release`.
The installer refuses an existing destination; install upgrades into a new
directory. The launcher configures Haiku FFI, native clipboard, watcher and HTTP
fallbacks, and paths for both PTY backends. Launch through `opencode`, not by
running the bundle without its environment. Runtime requirements are Node 24+,
Haiku system libraries, and ripgrep for efficient search; compiler toolchains
are not needed for ordinary use of the installed archive.

## 9. Configure a workspace, shared backend, TUI and browser

The supplied [text-only configuration](../examples/haiku-local-chat.json) matches
the verified endpoint and disables tools for the initial inference test.
Copy it as `opencode.json` in a disposable workspace:

```sh
mkdir -p /boot/home/opencode-work
cp /boot/home/opencode-haiku-src/examples/haiku-local-chat.json \
  /boot/home/opencode-work/opencode.json
mkdir -p /boot/home/opencode-profile/data /boot/home/opencode-profile/config \
  /boot/home/opencode-profile/cache /boot/home/opencode-profile/state
```

In **each OpenCode Terminal**, set the same profile and backend credential:

```sh
OC=/boot/home/opencode-haiku-2.0.29-haiku.5
export XDG_DATA_HOME=/boot/home/opencode-profile/data
export XDG_CONFIG_HOME=/boot/home/opencode-profile/config
export XDG_CACHE_HOME=/boot/home/opencode-profile/cache
export XDG_STATE_HOME=/boot/home/opencode-profile/state
export OPENCODE_PASSWORD='replace-with-your-own-local-test-password'
cd /boot/home/opencode-work
```

First Terminal:

```sh
"$OC/opencode" serve --hostname 127.0.0.1 --port 18083
```

Second Terminal:

```sh
"$OC/opencode" --server http://127.0.0.1:18083
```

Ask `Reply with OK only.` Then exit the TUI with Ctrl-C and restore using:

```sh
"$OC/opencode" --server http://127.0.0.1:18083 --continue
```

For WebPositive, issue a pairing code **on the same running backend**:

```sh
curl -fS -X POST -u "opencode:$OPENCODE_PASSWORD" \
  http://127.0.0.1:18083/api/pair -o /tmp/opencode-pair.json
node -e 'const fs=require("node:fs");const r=JSON.parse(fs.readFileSync("/tmp/opencode-pair.json","utf8"));const code=r.code??r.data?.code;if(!code)throw Error("Missing pairing code");console.log("http://127.0.0.1:18083/auth/connect/"+code)'
rm /tmp/opencode-pair.json
```

Open the printed link in WebPositive inside Haiku. Codes expire after five
minutes and work once. Do not save credentials/pairing codes in Git. This API
procedure targets the explicit shared `serve` process. The upstream `opencode
pair` command ensures a background service; do not invoke it casually alongside
an already owned profile, because it may create a second backend.

Open the TUI-created session in the browser, submit a follow-up, and check that
the same session updates in the TUI. One SQLite profile must have **one backend**.
The TUI and GUI are clients of it. Stop the backend separately with Ctrl-C.

For a real coding experiment, copy the text-only config, enable the model's
`capabilities.tools`, select the `build` agent, set output limit/body max_tokens
to 256, and replace the deny-all rule with narrow read/edit/shell permissions
for a disposable workspace. Preserve the text-only control config. Inspect
`tools/tui-port/coding-workflow.mjs` for the measured bounded fixture and its
permission syntax. That runner currently assumes the development guest paths
and transfer service; it is not a portable one-command T7610 installer.

## 10. Complete OpenCode source rebuild (optional)

### 10.1 Linux build tools and pinned sources

Need an x86_64 Linux build host with curl, git, patch, tar, unzip, Python 3.12+
(scripts use tarfile data filters), and enough disk space for source/dependency
caches. All tools can live under this repository; host sudo is unnecessary.
Bun 1.4.2 is the build-time JS runtime; Node 24+ is the Haiku runtime. Zig 0.16.0
builds the renderer/parser. Do not replace these pins with latest versions.

| Source/tool | Required revision/version | Archive/download |
|---|---|---|
| OpenCode | `34d8ded0c58dd66808c1d60e081e8c66da12a896` | `https://codeload.github.com/anomalyco/opencode/tar.gz/34d8ded0c58dd66808c1d60e081e8c66da12a896` |
| OpenTUI | `6f0efd3330978d696b42db3d7d95d2042008312b` | `https://codeload.github.com/anomalyco/opentui/tar.gz/6f0efd3330978d696b42db3d7d95d2042008312b` |
| Bun | 1.4.2 Linux x64 | `https://github.com/oven-sh/bun/releases/download/bun-v1.4.2/bun-linux-x64.zip` |
| Zig | 0.16.0 Linux x64 | `https://ziglang.org/download/0.16.0/zig-x86_64-linux-0.16.0.tar.xz` |
| Koffi | 3.3.3 | `https://registry.npmjs.org/koffi/-/koffi-3.3.3.tgz` |
| Persistent PTY | `878aa26ab1916f8d41a0ccb90d55a372d01abf69` (0.2.0) | `https://codeload.github.com/anomalyco/opencode-pty/tar.gz/878aa26ab1916f8d41a0ccb90d55a372d01abf69` |
| Ghostty VT | `ab0b9da9e88fcb4b0533a1854e84628f663930af` | `https://codeload.github.com/ghostty-org/ghostty/tar.gz/ab0b9da9e88fcb4b0533a1854e84628f663930af` |
| Node PTY | 1.2.0-beta.12 | `https://registry.npmjs.org/node-pty/-/node-pty-1.2.0-beta.12.tgz` |
| Node addon API | 7.1.0 | `https://registry.npmjs.org/node-addon-api/-/node-addon-api-7.1.0.tgz` |
| Undici | 7.29.0 | Installed by pinned OpenCode `bun.lock`; included by packager |

Download using `curl -fL URL -o PATH` to the paths in
`reference/TUI-PORT-INPUTS.json`, `reference/PTY-PORT-INPUTS.json`, and
`tools/opencode-port/build.sh`. Verify SHA-256 **before extracting**. Additional
Node PTY archive hashes: `45a012e37699bb70c9050cbf2e06e71b0b842de4cda58e938e3de973f6d5a36a`
and Node addon API `8e621f150678b183225c394c0faca7338396eb4fa620b447b88995f8990af522`.
Bun zip SHA-256 is `36368faef7527875d5ffa52e53cd48021741f2a83eb6208a8dd64068d422a913`.

Extract OpenCode/OpenTUI/Ghostty archives under `source/`, preserving their
commit-suffixed top-level names. Extract Bun to `cache/build-tools/bun-1.4.2/`
and Zig to `cache/build-tools/zig-x86_64-linux-0.16.0/`. Make `bun` executable.
Extract Koffi to `source/koffi-3.3.3/package/`. The older
`tools/opencode-port/build.sh` fetches OpenCode/Bun and builds the **headless**
archive; it does not bootstrap the full TUI dependencies. Use the full build
command in 10.5 after preparing all native inputs.

### 10.2 Export the Haiku SDK and build Koffi/clipboard

Apply `reference/koffi-portability.patch` with `patch -p1` in the extracted
Koffi `package` directory, then copy that directory into Haiku. **Haiku:**

```sh
cd /boot/home/native-build/koffi
node cnoke.cjs clean -P . -D src/koffi --release
MAKEFLAGS=-j2 node cnoke.cjs -P . -D src/koffi --release
find build -name koffi.node
```

Copy the resulting `build/koffi/haiku_x64/koffi.node` to the Linux repository's
`cache/opencode-final-koffi.node`. A clean build avoids stale x86-64-v2 objects.
Build the clipboard helper from this repo **in Haiku**:

```sh
g++ -O2 /boot/home/opencode-haiku-src/tools/tui-port/haiku-clipboard.cpp \
  -lbe -o /boot/home/native-build/haiku-clipboard
```

Copy it to Linux `cache/haiku-clipboard`. Export SDKs **in Haiku**:

```sh
cd /boot/home/native-build
tar -chzf haiku-sdk.tar.gz -C /boot/system/develop headers lib
gcc_lib_dir=$(dirname "$(gcc -print-file-name=libgcc.a)")
(cd "$gcc_lib_dir" && tar -chzf /boot/home/native-build/gcc-sdk.tar.gz \
  include libgcc* libstdc++* crt*.o)
```

Transfer these archives into Linux `cache/haiku-sdk.tar.gz` and
`cache/opencode-haiku-gcc-sdk.tar.gz`. Extract the first into `cache/haiku-sdk/`
and the second into `cache/haiku-sdk/gcc/`. Generate `cache/haiku-libc.txt` with
**absolute paths to your own clone**, not the development machine's paths:

```text
include_dir=ABSOLUTE_REPO/cache/haiku-sdk/headers/posix
sys_include_dir=ABSOLUTE_REPO/cache/haiku-sdk/headers/posix
crt_dir=ABSOLUTE_REPO/cache/haiku-sdk/lib
msvc_lib_dir=
kernel32_lib_dir=
gcc_dir=ABSOLUTE_REPO/cache/haiku-sdk/gcc
```

`build_native.sh` verifies the recorded SDK/addon hashes. A freshly generated
SDK archive can differ even with the same platform. Record its revision,
packages, archive SHA-256 and size and deliberately update the relevant entries
in `reference/TUI-PORT-INPUTS.json`; do not disable the checks or pretend it is
the original SDK. A newly built addon likewise needs its own provenance/hash.

### 10.3 Build the persistent terminal parser and daemon

**Linux:**

```sh
sh tools/tui-port/build_native.sh
sh tools/tui-port/build_parser.sh
```

The first applies the recorded Haiku Zig I/O changes and OpenTUI native/JS
patches. The second builds the scalar static Ghostty VT parser. Transfer
`cache/ghostty-haiku/lib/libghostty-vt.a` to `/boot/home/native-build/pty-lib/`.
Verify its source/configuration and hash; the recorded parser SHA-256 is
`44fd3d15ae62e94315a0ee6aa91b77994a42cb0649573a1d6d42c208e029f2f2`.

Extract the pinned pristine daemon source, and apply **all three** patches in
order with `patch -p1` from its root:

```text
reference/opencode-pty-haiku-build.patch
reference/opencode-pty-haiku-tests.patch
reference/opencode-pty-haiku-eof.patch
```

Copy the patched tree to `/boot/home/native-build/opencode-pty`. Do not use the
earlier generated `share/opencode-pty-haiku-source.tar.gz` as a complete final
patch set: its historical manifest predates the test-path and EOF fixes.
**Haiku, a new Terminal:**

```sh
unset LIBRARY_PATH
export CARGO_HOME=/boot/home/native-build/cargo-cache
export CARGO_TARGET_DIR=/boot/home/native-build/cargo-target
export OPENCODE_HAIKU_GHOSTTY_LIB=/boot/home/native-build/pty-lib
export CARGO_INCREMENTAL=0
cd /boot/home/native-build/opencode-pty
cargo build --locked --jobs 1
cargo test --locked --jobs 1 -- --test-threads=1
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cp "$CARGO_TARGET_DIR/debug/opencode-pty" /boot/home/native-build/opencode-pty-bin
strip --strip-debug /boot/home/native-build/opencode-pty-bin
```

Expect 54 passing native tests at the recorded source/patch set. This is a
debug Rust build with a ReleaseFast scalar parser, not a Release Rust binary.
Setting only `/boot/system/lib` in `LIBRARY_PATH` hid `librustc_driver`; leave
Cargo's environment paths alone. Disabling incremental builds avoided BFS
hard-link warnings during Clippy. Downloaded Rust dependencies use `Cargo.lock`.

### 10.4 Build the browser's separate Node PTY binding

Extract npm `node-pty` and `node-addon-api` packages, removing their outer
`package/` component, to `/boot/home/native-build/node-pty` and
`/boot/home/native-build/node-addon-api`. Apply `reference/node-pty-haiku.patch`
with `patch -p1` in the Node PTY root. **Haiku:**

```sh
cd /boot/home/native-build
mkdir -p node-pty/build/Release
g++ -std=c++17 -D_DEFAULT_SOURCE -O2 -fPIC -shared -pthread -DNAPI_VERSION=8 \
  -I/boot/system/develop/headers/node -I/boot/home/native-build/node-addon-api \
  node-pty/src/unix/pty.cc -lbsd -o node-pty/build/Release/pty.node
```

Keep the upstream Node PTY `lib/` JavaScript and `package.json` beside the
addon. These are needed at runtime. The Rust daemon and Node PTY are separate
backends; including one does not replace the other.

Transfer to Linux:

```text
Haiku opencode-pty-bin  -> cache/pty-runtime/opencode-pty (executable)
Haiku node-pty/         -> cache/pty-runtime/node-pty/
```

### 10.5 Build and package the full OpenCode runtime

**Linux repository root:**

```sh
sh tools/tui-port/build_bundle.sh > logs/full-build.log 2>&1
cat results/opencode-tui-package.json
sha256sum share/opencode-haiku-tui-2.0.29-haiku.5.tar.gz
```

Create `logs/` and `share/` first. This command builds OpenTUI with Bun, installs
its patched JS into the pinned OpenCode dependency, applies the headless and
terminal patches, builds the Node bundle/GUI assets and packages the native
runtime inputs. It uses frozen dependency locks and disables dependency install
scripts. It restores three pinned files in the ignored source tree before
applying overlapping patches; use that tree only as disposable build input.

The package must contain the launcher, JS bundle/assets, native renderer,
Koffi addon/wrapper, clipboard helper/backend, Undici, native daemon and Node
PTY binding. Use section 8 with the **new manifest checksum** and a new install
directory. The old `deploy_guest.sh` targets development paths and an older
archive; the checksum installer is the portable installation route.

## 11. T7610 acceptance and speed comparison

Run sequentially, with compilation and other inference jobs stopped:

1. Record guest revision, package versions, actual CPU model/features, RAM,
   vCPUs, hypervisor acceleration and launch configuration.
2. Record repository commit/dirty state, source/patch hashes, native binary
   hashes, model checksum and complete model-server command.
3. Pass native llama tests and model health; pass the OpenCode self-test.
4. Submit the same three fresh inference controls: OK-only; Python `add(a,b)`
   returning their sum, code only; `7 + 5`, number only. Use the same request
   bodies as `results/inference-compare-haiku.json` and seed 1234.
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
read [T7610-NEXT-RUN.md](T7610-NEXT-RUN.md).
