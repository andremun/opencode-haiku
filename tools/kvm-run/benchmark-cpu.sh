#!/bin/sh
# Native CPU-only llama-bench matrix; no server/port changes and no GPU backend.
set -eu
[ "$(uname -s)" = Haiku ] || { echo "Run this script in the Haiku guest." >&2; exit 2; }
H=${OPENCODE_LLAMA_WORK:-/boot/home/haiku-llm}
cd "$H"
repetitions=${OPENCODE_BENCH_REPS:-3}
# OPENCODE_BENCH_PROFILES: space-separated build-cpu-* names (default: baseline ivybridge).
case "$repetitions" in 1|2|3|4|5) ;; *) echo 'OPENCODE_BENCH_REPS must be 1..5.' >&2; exit 2;; esac
if curl -s --max-time 2 -o /dev/null http://127.0.0.1:18081/health; then
 echo 'Stop your owned guest model server before this uncontended benchmark.' >&2; exit 1
fi
model=$H/models/Qwen3-1.7B-Q4_K_M.gguf
printf '%s  %s\n' 72c5c3cb38fa32d5256e2fe30d03e7a64c6c79e668ad84057e3bd66e250b24fb "$model" | sha256sum -c -
result=$H/cpu-benchmark-$(date +%Y%m%d-%H%M%S)
mkdir "$result"
uname -a > "$result/platform.txt"
for profile in ${OPENCODE_BENCH_PROFILES:-baseline ivybridge}; do
 build=$H/build-cpu-$profile
 test -x "$build/bin/llama-bench"
 cp "$build/artifact-hashes.txt" "$result/$profile-build-hashes.txt"
 export LIBRARY_PATH="$build/bin:/boot/system/lib"
 for shape in 128:32 512:128; do
  batch=${shape%:*}; ubatch=${shape#*:}
  printf '%s\n' "$build/bin/llama-bench -m $model -ngl 0 -t 2 -p 512 -n 64 -b $batch -ub $ubatch -r $repetitions -o json" > "$result/$profile-$batch-command.txt"
  "$build/bin/llama-bench" -m "$model" -ngl 0 -t 2 -p 512 -n 64 -b "$batch" -ub "$ubatch" -r $repetitions -o json > "$result/$profile-$batch.json" 2> "$result/$profile-$batch.log"
 done
done
echo "CPU_BENCHMARK_DONE $result (synthetic prompt/decode throughput; not OpenCode latency)"
