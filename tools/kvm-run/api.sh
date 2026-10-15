#!/bin/sh
# Run independent probes and retain their actual Node status before any upload.
set -eu
W=${OPENCODE_ACCEPTANCE_WORK:-/boot/home/opencode-acceptance}
OC=${OPENCODE_PORT_ROOT:-/boot/home/opencode-haiku-2.0.29-haiku.5}
mkdir -p "$W/t"
cd "$W/t"
for f in api-workflow.mjs legacy-pty-api.mjs persistent-terminal-api.mjs; do curl -fsS --max-time 60 "http://10.0.2.2:18080/$f" -o "$f"; done
for path in "$W/http-port" "$W/node-pty"; do
 if [ -e "$path" ] && [ ! -L "$path" ]; then echo "Refusing to replace existing directory: $path" >&2; exit 2; fi
done
ln -sfn "$OC" "$W/http-port"
ln -sfn "$OC/node-pty" "$W/node-pty"
export LIBRARY_PATH=/boot/system/lib
failed=0
for name in api-workflow legacy-pty-api persistent-terminal-api; do
 echo "### $name"
 date
 if [ "$name" = persistent-terminal-api ]; then
  if node "$name.mjs" "$W" "$OC/opencode" > "$W/$name-run.log" 2>&1; then rc=0; else rc=$?; fi
 else
  if node "$name.mjs" "$W" > "$W/$name-run.log" 2>&1; then rc=0; else rc=$?; fi
 fi
 cat "$W/$name-run.log"
 echo "$name exit=$rc"
 [ "$rc" -eq 0 ] || failed=1
 if ! curl -fsS --max-time 30 -o /dev/null -X PUT --data-binary @"$W/$name-run.log" "http://10.0.2.2:18080/jobapi-$name.log"; then failed=1; fi
done
if [ "$failed" -ne 0 ]; then echo API-TESTS-FAILED >&2; exit 1; fi
echo API-TESTS-DONE
