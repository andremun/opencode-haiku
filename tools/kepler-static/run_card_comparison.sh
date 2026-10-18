#!/bin/bash
# ON-CARD comparison: deployed nvcc-built libggml-cuda against the Clang-built one (same source, same test binaries).
# PAUSES llama-server-one.service (a user unit; no sudo) and ALWAYS restarts it (exit trap plus a dead-man timer).
# Uses only the K40c named in that unit (never the card at 04:00.0). NOT RUN YET: it needs the user's go-ahead
# and a permission for the service pause (the agent's auto-mode classifier blocked it on 2026-10-19).
# Usage: run_card_comparison.sh OUTPUT_DIR
set -u
OUT=${1:?output directory}
SVC=llama-server-one.service
D=$HOME/llm-server/llama.cpp/build/bin
LIB_CLANG=$HOME/kepler-llvm-eval/lib-clang
UUID=$(sed -n 's/^Environment=CUDA_VISIBLE_DEVICES=//p' "$HOME/.config/systemd/user/$SVC")
MODEL=$HOME/llm-server/models/Qwen3.5-9B-UD-Q4_K_XL.gguf
NUMA=$HOME/.local/bin/numactl
FAILSAFE=k40-restore-failsafe
mkdir -p "$OUT"
log() { echo "$(date +%T) $*" | tee -a "$OUT/run.log"; }
restore() {
  log "restoring $SVC"
  systemctl --user start "$SVC"
  for i in $(seq 1 180); do
    if curl -fs --max-time 3 http://127.0.0.1:8080/health >/dev/null 2>&1; then log "service healthy after about $((i*10)) s"; break; fi
    sleep 10
  done
  { curl -s --max-time 5 http://127.0.0.1:8080/v1/models | head -c 300; echo; systemctl --user show "$SVC" -p ActiveState -p MainPID; } >> "$OUT/run.log" 2>&1
  systemctl --user stop "$FAILSAFE.timer" 2>/dev/null
  log "restore finished"
}
[ -n "$UUID" ] || { echo "No CUDA_VISIBLE_DEVICES in the unit"; exit 2; }
trap restore EXIT
systemd-run --user --quiet --on-active=150m --unit="$FAILSAFE" systemctl --user start "$SVC" || log "failsafe timer not created"
log "pausing $SVC (UUID $UUID)"
{ systemctl --user show "$SVC" -p ActiveState -p MainPID; curl -s --max-time 5 http://127.0.0.1:8080/health; echo; } >> "$OUT/run.log" 2>&1
systemctl --user stop "$SVC"
sleep 8
nvidia-smi --query-gpu=uuid,name,memory.used,memory.total,temperature.gpu,utilization.gpu,clocks.sm,clocks.max.sm --format=csv > "$OUT/gpu-before.csv" 2>&1
used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$UUID" 2>/dev/null | tr -d ' ')
log "card memory in use after pause: ${used:-unknown} MiB"
if [ -z "${used:-}" ] || [ "$used" -gt 1500 ]; then log "card not idle; aborting"; exit 3; fi

run() {  # run NAME LIBDIR TIMEOUT COMMAND...
  local name=$1 libdir=$2 tmo=$3; shift 3
  env CUDA_VISIBLE_DEVICES="$UUID" LD_LIBRARY_PATH="$libdir" "$NUMA" --cpunodebind=0 --membind=0 timeout "$tmo" "$@"
}
telemetry() { nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader -i "$UUID" >> "$OUT/telemetry.csv" 2>&1; }

# 1. correctness against the CPU backend, per operation
OPS="MUL_MAT MUL_MAT_ID FLASH_ATTN_EXT SOFT_MAX RMS_NORM ROPE GET_ROWS CPY SCALE ADD MUL UNARY GLU ARGSORT TOP_K SUM_ROWS CONCAT"
for op in $OPS; do
  for variant in nvcc clang; do
    libdir=$D; [ $variant = clang ] && libdir=$LIB_CLANG
    run $variant "$libdir" 900 "$D/test-backend-ops" test -b CUDA0 -o "$op" > "$OUT/test-$op-$variant.log" 2>&1
    log "test $op $variant rc=$? $(grep -E 'tests passed|passed' "$OUT/test-$op-$variant.log" | tail -1 | cut -c1-80)"
  done
  telemetry
done

# 2. kernel performance, A-B-A to expose drift
for op in MUL_MAT MUL_MAT_ID FLASH_ATTN_EXT; do
  for variant in nvcc clang nvcc2; do
    libdir=$D; [ $variant = clang ] && libdir=$LIB_CLANG
    run $variant "$libdir" 1500 "$D/test-backend-ops" perf -b CUDA0 -o "$op" > "$OUT/perf-$op-$variant.log" 2>&1
    log "perf $op $variant rc=$?"
    telemetry
  done
done

# 3. end to end: Qwen3.5-9B Q4_K_XL fully on the card, A-B-A
for variant in nvcc clang nvcc2; do
  libdir=$D; [ $variant = clang ] && libdir=$LIB_CLANG
  run $variant "$libdir" 1500 "$D/llama-bench" -m "$MODEL" -ngl 99 -fa 1 -p 512 -n 128 -r 3 -o json > "$OUT/bench-$variant.json" 2> "$OUT/bench-$variant.err"
  log "llama-bench $variant rc=$?"
  telemetry
done
nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv > "$OUT/gpu-after.csv" 2>&1
log "tests finished; restoring service via exit trap"
