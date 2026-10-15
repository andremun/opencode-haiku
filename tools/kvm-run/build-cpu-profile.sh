#!/bin/sh
# Haiku guest only: build separate pinned CPU variants; do not replace the installed baseline.
set -eu
[ "$(uname -s)" = Haiku ] || { echo "Run this script in the Haiku guest." >&2; exit 2; }
profile=${1:-baseline}
case "$profile" in baseline|ivybridge) ;; *) echo 'Usage: build-cpu-profile.sh baseline|ivybridge' >&2; exit 2;; esac
H=${OPENCODE_LLAMA_WORK:-/boot/home/haiku-llm}
PORT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$H"
printf '%s\n' '6980c77f4ad311bca845848f5b899d1a68b35dec94de849ca1b2ce4bc3ca0a3a  llama-source.tar.gz' | sha256sum -c -
for p in kepler-sm35-ggml-cuda reasoning-budget-rearm haiku-portability; do
 (cd llama && git apply --reverse --check "$PORT/reference/llama-cpu/$p.patch")
done
build=$H/build-cpu-$profile
mkdir -p "$build"
uname -a > "$build/platform.txt"
if [ "$profile" = ivybridge ]; then
 cat > "$build/check-avx.c" <<'C'
#include <stdio.h>
int main(void) {
#if defined(__x86_64__) && defined(__GNUC__)
    __builtin_cpu_init();
    if (__builtin_cpu_supports("avx") && __builtin_cpu_supports("f16c") && __builtin_cpu_supports("sse4.2")) {
        puts("AVX/F16C/SSE4.2 usable in this guest"); return 0;
    }
#endif
    fputs("Required guest CPU/OS features are unavailable\n", stderr); return 1;
}
C
 gcc "$build/check-avx.c" -o "$build/check-avx"
 "$build/check-avx" >> "$build/platform.txt"
 avx=ON
else avx=OFF; fi
cmake -S llama -B "$build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
 -DGGML_NATIVE=OFF -DGGML_SSE42="$avx" -DGGML_AVX="$avx" -DGGML_F16C="$avx" \
 -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_BMI2=OFF -DGGML_AVX512=OFF -DGGML_AVX_VNNI=OFF \
 -DGGML_CUDA=OFF -DGGML_OPENMP=OFF -DLLAMA_OPENSSL=OFF -DLLAMA_BUILD_WEBUI=OFF -DLLAMA_BUILD_TESTS=ON
cmake --build "$build" --parallel 2 --target llama-server llama-bench test-reasoning-budget test-chat-template
export LIBRARY_PATH="$build/bin:/boot/system/lib"
"$build/bin/test-reasoning-budget"
"$build/bin/test-chat-template"
sha256sum "$build/bin/llama-server" "$build/bin/llama-bench" "$build/CMakeCache.txt" "$build/compile_commands.json" > "$build/artifact-hashes.txt"
echo "CPU_PROFILE_PASS $profile (performance not yet measured)"
