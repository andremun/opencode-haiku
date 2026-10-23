#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Start a shared OpenCode backend on 127.0.0.1:18083 for interactive clients (TUI, browser) using a
# free cloud model on a fresh copy of the synthetic cloud task. Haiku guest only.
# Usage: with-cloud-key-guest.sh KEY_URL sh cloud-serve.sh WORK_DIR [MODEL]
# The key stays in the backend's environment only. WORK_DIR/fixture is the project; the backend PID
# is written to WORK_DIR/serve.pid. Stop it with: kill "$(cat WORK_DIR/serve.pid)".
set -eu
[ "$(uname -s)" = Haiku ] || { echo 'Run this script in the Haiku guest.' >&2; exit 2; }
[ "$#" -ge 1 ] || { echo 'Usage: cloud-serve.sh WORK_DIR [MODEL]' >&2; exit 2; }
[ -n "${OPENCODE_API_KEY:-}" ] || { echo 'OPENCODE_API_KEY is not set (use with-cloud-key-guest.sh).' >&2; exit 2; }
guest=${OPENCODE_GUEST_HOME:-/boot/home}
SRC=${OPENCODE_SOURCE_ROOT:-$guest/opencode-haiku-src}
work=$1
model=${2:-opencode/glm-5.3-flash-free}
case "$model" in */big-pickle|*-free) ;; *) echo "Refusing a non-free model ($model)." >&2; exit 2;; esac
if curl -s --max-time 2 -o /dev/null http://127.0.0.1:18083/; then
 echo 'Port 18083 already has an HTTP listener; refusing a second backend.' >&2
 exit 1
fi
[ ! -e "$work" ] || { echo "Work directory exists: $work" >&2; exit 2; }
mkdir -p "$work/fixture"
cp -R "$SRC/examples/cloud-task/start/." "$work/fixture/"
# Same scoped permissions as tests/acceptance/cloud-coding-task.mjs.
cat > "$work/fixture/opencode.json" <<EOF
{"model":"$model","update":"disable","share":"disabled","snapshots":false,"formatter":false,"lsp":false,
 "permissions":[{"action":"*","resource":"*","effect":"deny"},{"action":"read","resource":"*","effect":"allow"},
  {"action":"edit","resource":"src/*","effect":"allow"},{"action":"shell","resource":"node --test*","effect":"allow"},
  {"action":"shell","resource":"tail *","effect":"allow"},{"action":"shell","resource":"head *","effect":"allow"}],
 "agents":{"build":{"model":"$model","steps":20}}}
EOF
(cd "$work/fixture/test" && sha256sum *) > "$work/tests.sha256"
. "$guest/opencode-env.sh"
OC=${OPENCODE_PORT_ROOT:-$OC}
case "${OPENCODE_PASSWORD:-}" in ''|CHOOSE-A-LOCAL-TEST-PASSWORD) echo "Set a local password in $guest/opencode-env.sh." >&2; exit 2;; esac
for name in data config cache state; do mkdir -p "$work/state/$name"; done
export XDG_DATA_HOME="$work/state/data" XDG_CONFIG_HOME="$work/state/config" XDG_CACHE_HOME="$work/state/cache" XDG_STATE_HOME="$work/state/state"
export LIBRARY_PATH=/boot/system/lib
cd "$work/fixture"
nohup "$OC/opencode" serve --hostname 127.0.0.1 --port 18083 > "$work/serve.log" 2>&1 &
pid=$!
printf '%s\n' "$pid" > "$work/serve.pid"
for attempt in $(seq 1 60); do
 kill -0 "$pid" 2>/dev/null || { echo 'Backend exited during startup.' >&2; exit 1; }
 if curl -fsS --max-time 3 -u "opencode:$OPENCODE_PASSWORD" http://127.0.0.1:18083/api/info >/dev/null; then
  echo "Backend ready: PID $pid, client $OC, model $model, project $work/fixture"
  exit 0
 fi
 sleep 2
done
kill "$pid" 2>/dev/null || true
echo 'Backend readiness deadline expired.' >&2
exit 1
