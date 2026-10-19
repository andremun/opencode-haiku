#!/bin/sh
# Guest-only owned services + inference + coding. No persistent PID-file cleanup.
set -eu
[ "$(uname -s)" = Haiku ] || { echo 'Run this script in the Haiku guest.' >&2; exit 2; }
guest=${OPENCODE_GUEST_HOME:-/boot/home}
SRC=${OPENCODE_SOURCE_ROOT:-$guest/opencode-haiku-src}
OC=${OPENCODE_PORT_ROOT:-$guest/opencode-haiku-2.0.29-haiku.5}
if [ "${1:-}" = --checks ]; then
 p=${2:?profile}
 . "$guest/opencode-env.sh"
 OC=${OPENCODE_PORT_ROOT:-$OC}
 cd /tmp
 node "$SRC/tools/tui-port/inference-compare.cjs" http://127.0.0.1:18081 "$guest/inference-$p.json" "jobinf-$p.json"
 mkdir -p "$guest/coding-$p"
 OPENCODE_TEST_PORT_ROOT="$OC/opencode" OPENCODE_TEST_STEPS=8 node "$SRC/tools/tui-port/coding-workflow.mjs" "$guest/coding-$p" > "$guest/coding-$p/run.log" 2>&1
 # coding-workflow records semantic failure separately from the client exit.
 node -e 'const o=require(process.argv[1]); if (!o.semantic_pass || o.expired || o.exit !== 0) process.exit(1)' "$guest/coding-$p/coding-outcome.json"
 cat "$guest/coding-$p/coding-outcome.json"
 exit 0
fi
p=${1:?Usage: prodrun.sh PROFILE}
case "$p" in installed|baseline|ivybridge|production|production-noomp) ;; *) echo 'Unknown CPU profile.' >&2; exit 2;; esac
OPENCODE_PORT_ROOT="$OC" OPENCODE_LLAMA_PROFILE="$p" OPENCODE_LLAMA_BATCH=512 OPENCODE_LLAMA_UBATCH=128
export OPENCODE_PORT_ROOT OPENCODE_LLAMA_PROFILE OPENCODE_LLAMA_BATCH OPENCODE_LLAMA_UBATCH
# services.sh retains its cleanup trap until these checks have exited.
exec sh "$SRC/tools/kvm-run/services.sh" sh "$SRC/tools/kvm-run/prodrun.sh" --checks "$p"
