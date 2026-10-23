# Build OpenCode for Haiku from source

Split from `T7610-HAIKU-SETUP.md` on 23 October 2026. Section numbers are those of that guide. "Section N" refers to them: sections 1 to 7, 11 and 12 are in [DEVELOP.md](DEVELOP.md), sections 8 and 9 in [INSTALL.md](INSTALL.md), section 10 in [BUILD.md](BUILD.md).

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

Run `make fetch`. It downloads each archive to the path in `reference/INPUTS.json` and
checks its SHA-256. Verify SHA-256 **before extracting**. Additional
Node PTY archive hashes: `45a012e37699bb70c9050cbf2e06e71b0b842de4cda58e938e3de973f6d5a36a`
and Node addon API `8e621f150678b183225c394c0faca7338396eb4fa620b447b88995f8990af522`.
Bun zip SHA-256 is `36368faef7527875d5ffa52e53cd48021741f2a83eb6208a8dd64068d422a913`.

Extract OpenCode/OpenTUI/Ghostty archives under `source/`, preserving their
commit-suffixed top-level names. Extract Bun to `cache/build-tools/bun-1.4.2/`
and Zig to `cache/build-tools/zig-x86_64-linux-0.16.0/`. Make `bun` executable.
Extract Koffi to `source/koffi-3.3.3/package/`. The headless-only build of port
`haiku.1` was removed on 23 October 2026 (Git history keeps it). Use the full build
command in 10.5 after preparing all native inputs.

### 10.2 Export the Haiku SDK and build Koffi/clipboard

Apply `patches/koffi/koffi-portability.patch` with `patch -p1` in the extracted
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
g++ -O2 /boot/home/opencode-haiku-src/src/haiku-clipboard.cpp \
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
sh build/build_native.sh
sh build/build_parser.sh
```

The first applies the recorded Haiku Zig I/O changes and OpenTUI native/JS
patches. The second builds the scalar static Ghostty VT parser. Transfer
`cache/ghostty-haiku/lib/libghostty-vt.a` to `/boot/home/native-build/pty-lib/`.
Verify its source/configuration and hash; the recorded parser SHA-256 is
`44fd3d15ae62e94315a0ee6aa91b77994a42cb0649573a1d6d42c208e029f2f2`.

Extract the pinned pristine daemon source, and apply **all three** patches in
order with `patch -p1` from its root:

```text
patches/opencode-pty/opencode-pty-haiku-build.patch
patches/opencode-pty/opencode-pty-haiku-tests.patch
patches/opencode-pty/opencode-pty-haiku-eof.patch
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
`/boot/home/native-build/node-addon-api`. Apply `patches/node-pty/node-pty-haiku.patch`
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
sh build/build_bundle.sh > logs/full-build.log 2>&1
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
