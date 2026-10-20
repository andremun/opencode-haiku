#!/bin/bash
# ON-CARD test of the Clang fixes and the hybrid libraries (nvcc objects plus selected Clang objects).
# Pauses llama-server-one.service; restoration follows confirmed worker termination (same supervisor and protocol as
# run_card_comparison.sh). Uses only the K40c named in that unit (never the card at 04:00.0).
# Usage: run_card_hybrid.sh --execute NEW_OUTPUT_DIR
# Explicit invocation is required; building or testing offline does not authorise a card run, and the user must allow
# this exact command (stopping the production service). Libraries come from ~/kepler-llvm-eval (see docs/KEPLER-HYBRID-*.md).
# Unlike the first runner this one CONTINUES after a failing test and records the exit code of every step.
set -euo pipefail
if [ "${1:-}" = --execute ] && [ "$#" -eq 2 ]; then
 exec python3 "$(dirname "$0")/card_supervisor.py" "$0" "$2"
fi
if [ "${OPENCODE_CARD_WORKER:-}" != 1 ]; then
 echo 'Usage (requires separate card/service authorisation): run_card_hybrid.sh --execute NEW_OUTPUT_DIR' >&2
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
K=$HOME/kepler-llvm-eval
UUID=$(sed -n 's/^Environment=CUDA_VISIBLE_DEVICES=//p' "$HOME/.config/systemd/user/$SVC")
MODEL=$HOME/llm-server/models/Qwen3.5-9B-UD-Q4_K_XL.gguf
NUMA=$HOME/.local/bin/numactl
[[ "$UUID" =~ ^GPU-[a-fA-F0-9-]+$ ]] || { echo 'Expected exactly one GPU UUID' >&2; exit 2; }
for program in systemctl timeout curl nvidia-smi sed grep; do command -v "$program" >/dev/null; done
for file in "$D/test-backend-ops" "$D/llama-bench" "$D/llama-server" "$NUMA"; do test -x "$file"; done
for file in "$MODEL" "$K/lib-nofinite/libggml-cuda.so.0" "$K/lib-nofast/libggml-cuda.so.0"; do test -r "$file"; done
systemctl --user is-active --quiet "$SVC"
: > "$MARKER"
log "pausing $SVC (UUID $UUID)"
timeout -k 5 60 systemctl --user stop "$SVC"
sleep 8
used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$UUID" | tr -d ' ')
[[ "$used" =~ ^[0-9]+$ ]] && [ "$used" -le 1500 ] || { log 'card not idle; aborting'; exit 3; }
nvidia-smi --query-gpu=uuid,name,memory.used,temperature.gpu,clocks.sm --format=csv > "$OUT/gpu-before.csv" 2>&1 || true

libdir_of() { case $1 in nvcc|nvcc2) echo "$D";; nofinite) echo "$K/lib-nofinite";; nofast) echo "$K/lib-nofast";; hybnofinite) echo "$K/lib-hyb-nofinite";; hybnofast) echo "$K/lib-hyb-nofast";; ieee) echo "$K/lib-ieee";; esac; }
avail() { [ "$1" = nvcc ] || [ "$1" = nvcc2 ] || [ -e "$(libdir_of "$1")/libggml-cuda.so.0" ]; }
run() {  # run LIBNAME TIMEOUT COMMAND...
  local libdir; libdir=$(libdir_of "$1"); local tmo=$2; shift 2
  env CUDA_VISIBLE_DEVICES="$UUID" LD_LIBRARY_PATH="$libdir" "$NUMA" --cpunodebind=0 --membind=0 timeout -k 5 "$tmo" "$@"
}
telemetry() { nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader -i "$UUID" >> "$OUT/telemetry.csv" 2>&1 || true; }
step() {  # step LABEL FILE LIBNAME TIMEOUT COMMAND...   (records the exit code, never stops the run)
  local label=$1 file=$2 lib=$3 tmo=$4; shift 4
  local rc=0
  run "$lib" "$tmo" "$@" > "$file" 2>&1 || rc=$?
  log "$label $lib rc=$rc $(sed 's/\x1b\[[0-9;]*m//g' "$file" | grep -E 'tests passed' | tail -1 | tr -s ' ' | cut -c1-60)"
  telemetry
}

# Selection (defaults give the full run; a short follow-up can narrow them, for example
#   HYBRID_CORR_LIBS='ieee nvcc' HYBRID_OPS='FLASH_ATTN_EXT SOFT_MAX' HYBRID_PERF=0 HYBRID_E2E=0 HYBRID_TEXT_LIBS='' ).
CORR_LIBS=${HYBRID_CORR_LIBS:-nvcc nofinite nofast hybnofinite hybnofast}
OPS=${HYBRID_OPS:-FLASH_ATTN_EXT SOFT_MAX MUL_MAT MUL_MAT_ID}
PERF_LIBS=${HYBRID_PERF_LIBS:-nvcc nofinite nofast hybnofinite hybnofast nvcc2}
E2E_LIBS=${HYBRID_E2E_LIBS:-nvcc nofinite nofast hybnofinite hybnofast nvcc2}
TEXT_LIBS=${HYBRID_TEXT_LIBS-nvcc nofinite nofast hybnofinite hybnofast}

# 1. correctness against the CPU backend: the failing attention case first
for op in $OPS; do
  for lib in $CORR_LIBS; do
    avail "$lib" || { log "skip $lib (not built)"; continue; }
    step "test $op" "$OUT/test-$op-$lib.log" "$lib" 900 "$D/test-backend-ops" test -b CUDA0 -o "$op"
  done
done

# 2. kernel performance (production quantisation types only), A-B-A for nvcc
if [ "${HYBRID_PERF:-1}" = 1 ]; then
  PT='type_a=(q4_K|q5_K|q6_K|q8_0)'
  for lib in $PERF_LIBS; do
    avail "$lib" || continue
    step "perf MUL_MAT" "$OUT/perf-MUL_MAT-$lib.log" "$lib" 900 "$D/test-backend-ops" perf -b CUDA0 -o MUL_MAT -p "$PT"
  done
  for lib in nvcc hybnofinite hybnofast nvcc2; do
    avail "$lib" || continue
    step "perf MUL_MAT_ID" "$OUT/perf-MUL_MAT_ID-$lib.log" "$lib" 900 "$D/test-backend-ops" perf -b CUDA0 -o MUL_MAT_ID -p "$PT"
  done
  for lib in $PERF_LIBS; do
    avail "$lib" || continue
    step "perf FLASH_ATTN_EXT" "$OUT/perf-FLASH_ATTN_EXT-$lib.log" "$lib" 900 "$D/test-backend-ops" perf -b CUDA0 -o FLASH_ATTN_EXT
  done
fi

# 3. end to end on Qwen3.5-9B Q4_K_XL (all layers on the card): speed, then greedy text through a short-lived server
if [ "${HYBRID_E2E:-1}" = 1 ]; then
  for lib in $E2E_LIBS; do
    avail "$lib" || continue
    rc=0
    run "$lib" 900 "$D/llama-bench" -m "$MODEL" -ngl 99 -fa 1 -p 512 -n 128 -r 3 -o json > "$OUT/bench-$lib.json" 2> "$OUT/bench-$lib.err" || rc=$?
    log "llama-bench $lib rc=$rc"; telemetry
  done
fi
text_check() {  # greedy 48-token completion through llama-server (llama-cli hung in the first run: do not use it)
  local lib=$1 ok=0 spid
  run "$lib" 300 "$D/llama-server" -m "$MODEL" -ngl 99 -fa on -c 512 --parallel 1 --host 127.0.0.1 --port 18181 --no-webui > "$OUT/text-$lib.server.log" 2>&1 &
  spid=$!
  for i in $(seq 1 60); do
    if curl -fs --max-time 3 http://127.0.0.1:18181/health >/dev/null 2>&1; then ok=1; break; fi
    sleep 2
  done
  if [ "$ok" = 1 ]; then
    curl -s --max-time 120 -H 'Content-Type: application/json' -d '{"prompt":"The three primary colours are","n_predict":48,"temperature":0,"top_k":1,"seed":1,"cache_prompt":false}' http://127.0.0.1:18181/completion > "$OUT/text-$lib.json" || true
  fi
  kill "$spid" 2>/dev/null || true
  wait "$spid" 2>/dev/null || true
  log "text $lib server_ready=$ok"; telemetry
}
for lib in $TEXT_LIBS; do
  avail "$lib" || continue
  text_check "$lib"
done
nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv -i "$UUID" > "$OUT/gpu-after.csv" 2>&1 || true
log 'tests finished; supervisor will reap workers before restoration'
