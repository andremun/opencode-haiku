#!/bin/sh
# Run the synthetic cloud coding task once per model, in order, with one key fetch.
# Usage (guest): with-cloud-key-guest.sh KEY_URL sh cloud-models.sh OUT_DIR MODEL [MODEL...]
# The key stays in this process environment only. Each run writes OUT_DIR/MODEL-NAME.log;
# OUT_DIR/summary.txt holds one line per model: name, runner exit, seconds.
set -u
[ "$#" -ge 2 ] || { echo 'Usage: cloud-models.sh OUT_DIR MODEL [MODEL...]' >&2; exit 2; }
[ -n "${OPENCODE_API_KEY:-}" ] || { echo 'OPENCODE_API_KEY is not set (use with-cloud-key-guest.sh).' >&2; exit 2; }
guest=${OPENCODE_GUEST_HOME:-/boot/home}
SRC=${OPENCODE_SOURCE_ROOT:-$guest/opencode-haiku-src}
OC=${OPENCODE_PORT_ROOT:-$guest/opencode-haiku-2.0.29-haiku.5}
out=$1; shift
mkdir -p "$out"
for model in "$@"; do
 name=$(printf '%s' "$model" | tr '/' '_')
 start=$(date +%s)
 OPENCODE_TEST_PORT_ROOT="$OC/opencode" OPENCODE_CLOUD_MODEL="$model" node "$SRC/tools/tui-port/cloud-coding-task.mjs" "$out/$name" > "$out/$name.log" 2>&1
 rc=$?
 printf '%s rc=%s seconds=%s\n' "$model" "$rc" "$(( $(date +%s) - start ))" >> "$out/summary.txt"
done
echo done >> "$out/summary.txt"
