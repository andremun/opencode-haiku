#!/bin/sh
# Usage: tools/job.sh N 'shell commands' [timeout_s]  -> runs in the Haiku guest, prints output
R=$(cd "$(dirname "$0")/.." && pwd); N=$1; printf '%s\n' "$2" > "$R/share/job$N.sh"; rm -f "$R/logs/job$N.out"
T=${3:-300}; i=0; while [ ! -f "$R/logs/job$N.out" ]; do sleep 2; i=$((i+2)); [ $i -ge $T ] && { echo TIMEOUT; exit 1; }; done; cat "$R/logs/job$N.out"
