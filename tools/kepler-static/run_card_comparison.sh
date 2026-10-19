#!/bin/bash
# ON-CARD comparison: deployed nvcc-built libggml-cuda against the Clang-built one (same source, same test binaries).
# Pauses llama-server-one.service; restoration follows confirmed worker termination.
# Uses only the K40c named in that unit (never the card at 04:00.0). NOT RUN YET: it needs the user's go-ahead
# and a permission for the service pause (the agent's auto-mode classifier blocked it on 2026-10-19).
# Usage: run_card_comparison.sh --execute NEW_OUTPUT_DIR
# Explicit invocation is required; preparation/testing does not authorise a card run.
# The supervisor drains all owned descendants before restoring the service.
# SIGKILL of the supervisor or an unkillable GPU task requires manual recovery.
set -euo pipefail
if [ "${1:-}" = --execute ] && [ "$#" -eq 2 ]; then
 exec python3 "$(dirname "$0")/card_supervisor.py" "$0" "$2"
fi
if [ "${OPENCODE_CARD_WORKER:-}" != 1 ]; then
 echo 'Usage (requires separate card/service authorisation): run_card_comparison.sh --execute NEW_OUTPUT_DIR' >&2
 exit 2
fi
mode=${1:?worker mode}
OUT=${2:?output directory}
SVC=llama-server-one.service
log() { echo "$(date +%T) $*" | tee -a "$OUT/run.log"; }
if [ "$mode" = --restore ]; then
 log "restoring $SVC after test process cleanup"
 timeout -k 5 60 systemctl --user start "$SVC"
 for i in $(seq 1 180); do
  if curl -fs --max-time 3 http://127.0.0.1:8080/health >/dev/null 2>&1; then
   log 'service healthy; restoration complete'
   exit 0
  fi
  sleep 10
 done
 log 'restoration health deadline expired'
 exit 1
fi
[ "$mode" = --worker ] || exit 2
MARKER=${3:?pause marker}
D=$HOME/llm-server/llama.cpp/build/bin
LIB_CLANG=$HOME/kepler-llvm-eval/lib-clang
UUID=$(sed -n 's/^Environment=CUDA_VISIBLE_DEVICES=//p' "$HOME/.config/systemd/user/$SVC")
MODEL=$HOME/llm-server/models/Qwen3.5-9B-UD-Q4_K_XL.gguf
NUMA=$HOME/.local/bin/numactl
# Preflight before any pause. Require exactly one UUID and an initially active
# service so cleanup cannot accidentally start a deliberately stopped service.
[[ "$UUID" =~ ^GPU-[a-fA-F0-9-]+$ ]] || { echo 'Expected exactly one GPU UUID' >&2; exit 2; }
for program in systemctl timeout curl nvidia-smi; do command -v "$program" >/dev/null; done
for file in "$D/test-backend-ops" "$D/llama-bench" "$NUMA"; do test -x "$file"; done
for file in "$MODEL" "$LIB_CLANG/libggml-cuda.so.0"; do test -r "$file"; done
systemctl --user is-active --quiet "$SVC"
# Write before attempting stop: a partial stop must still trigger restoration.
: > "$MARKER"
log "pausing $SVC (UUID $UUID)"
timeout -k 5 60 systemctl --user stop "$SVC"
sleep 8
used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$UUID" | tr -d ' ')
[[ "$used" =~ ^[0-9]+$ ]] && [ "$used" -le 1500 ] || { log 'card not idle; aborting'; exit 3; }

run() {  # run NAME LIBDIR TIMEOUT COMMAND...
  local name=$1 libdir=$2 tmo=$3; shift 3
  env CUDA_VISIBLE_DEVICES="$UUID" LD_LIBRARY_PATH="$libdir" "$NUMA" --cpunodebind=0 --membind=0 timeout -k 5 "$tmo" "$@"
}
telemetry() { nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader -i "$UUID" >> "$OUT/telemetry.csv" 2>&1; }

# 1. correctness against the CPU backend, per operation
OPS="MUL_MAT MUL_MAT_ID FLASH_ATTN_EXT SOFT_MAX RMS_NORM ROPE GET_ROWS CPY SCALE ADD MUL UNARY GLU ARGSORT TOP_K SUM_ROWS CONCAT"
for op in $OPS; do
  for variant in nvcc clang; do
    libdir=$D; [ $variant = clang ] && libdir=$LIB_CLANG
    run $variant "$libdir" 900 "$D/test-backend-ops" test -b CUDA0 -o "$op" > "$OUT/test-$op-$variant.log" 2>&1
    log "test $op $variant passed"
  done
  telemetry
done

# 2. kernel performance, A-B-A to expose drift
for op in MUL_MAT MUL_MAT_ID FLASH_ATTN_EXT; do
  for variant in nvcc clang nvcc2; do
    libdir=$D; [ $variant = clang ] && libdir=$LIB_CLANG
    run $variant "$libdir" 1500 "$D/test-backend-ops" perf -b CUDA0 -o "$op" > "$OUT/perf-$op-$variant.log" 2>&1
    log "perf $op $variant passed"
    telemetry
  done
done

# 3. end to end: Qwen3.5-9B Q4_K_XL fully on the card, A-B-A
for variant in nvcc clang nvcc2; do
  libdir=$D; [ $variant = clang ] && libdir=$LIB_CLANG
  run $variant "$libdir" 1500 "$D/llama-bench" -m "$MODEL" -ngl 99 -fa 1 -p 512 -n 128 -r 3 -o json > "$OUT/bench-$variant.json" 2> "$OUT/bench-$variant.err"
  log "llama-bench $variant passed"
  telemetry
done
nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv -i "$UUID" > "$OUT/gpu-after.csv" 2>&1
log "tests finished; supervisor will reap workers before restoration"
