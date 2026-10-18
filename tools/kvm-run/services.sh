#!/bin/sh
# Start only this test stack; preserve existing configuration and refuse duplicate listeners.
set -eu
[ "$(uname -s)" = Haiku ] || { echo "Run this script in the Haiku guest." >&2; exit 2; }
for port in 18081 18083; do
 if curl -s --max-time 2 -o /dev/null "http://127.0.0.1:$port/health"; then
  echo "Port $port already has an HTTP listener; refusing duplicate services." >&2
  exit 1
 fi
done
mkdir -p /boot/home/opencode-work /boot/home/opencode-profile/data /boot/home/opencode-profile/config /boot/home/opencode-profile/cache /boot/home/opencode-profile/state
if [ ! -e /boot/home/opencode-work/opencode.json ]; then
 cp /boot/home/opencode-haiku-src/examples/haiku-local-chat.json /boot/home/opencode-work/opencode.json
fi
if [ ! -e /boot/home/opencode-env.sh ]; then
 umask 077
 password=$(node -e 'console.log(require("node:crypto").randomBytes(24).toString("hex"))')
 cat > /boot/home/opencode-env.sh <<EE
OC=/boot/home/opencode-haiku-2.0.29-haiku.5
export XDG_DATA_HOME=/boot/home/opencode-profile/data XDG_CONFIG_HOME=/boot/home/opencode-profile/config XDG_CACHE_HOME=/boot/home/opencode-profile/cache XDG_STATE_HOME=/boot/home/opencode-profile/state
export OPENCODE_PASSWORD='$password'
cd /boot/home/opencode-work
EE
fi
. /boot/home/opencode-env.sh
OC=${OPENCODE_PORT_ROOT:-$OC}
case "${OPENCODE_PASSWORD:-}" in ''|CHOOSE-A-LOCAL-TEST-PASSWORD) echo 'Set a real local password in /boot/home/opencode-env.sh before starting.' >&2; exit 2;; esac
model_pid=
backend_pid=
cleanup() {
 [ -z "$backend_pid" ] || kill "$backend_pid" 2>/dev/null || true
 [ -z "$model_pid" ] || kill "$model_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
H=${OPENCODE_LLAMA_WORK:-/boot/home/haiku-llm}
# Default: Ivy Bridge, OpenMP off (adopted 2026-10-18, see docs/KVM-VM.md). Build it with
# build-cpu-profile.sh ivybridge. Use OPENCODE_LLAMA_PROFILE=installed|baseline for the SSE2 build.
profile=${OPENCODE_LLAMA_PROFILE:-ivybridge}
case "$profile" in
 installed) binary=$H/build/bin/llama-server;;
 baseline|ivybridge|production|production-noomp) binary=$H/build-cpu-$profile/bin/llama-server;;
 *) echo 'Unknown CPU profile.' >&2; exit 2;;
esac
[ -x "$binary" ] || { echo "llama-server for profile '$profile' not built: $binary (run tools/kvm-run/build-cpu-profile.sh $profile)" >&2; exit 2; }
batch=${OPENCODE_LLAMA_BATCH:-128}
ubatch=${OPENCODE_LLAMA_UBATCH:-32}
for value in "$batch" "$ubatch"; do case "$value" in ''|*[!0-9]*|0) echo 'Batch sizes must be positive integers.' >&2; exit 2;; esac; done
cd "$H"
export LIBRARY_PATH="$(dirname "$binary"):/boot/system/lib"
nohup "$binary" -m models/Qwen3-1.7B-Q4_K_M.gguf -ngl 0 -t 2 -tb 2 -b "$batch" -ub "$ubatch" -c 4096 --parallel 1 --poll 0 --poll-batch 0 --cache-ram 128 --host 127.0.0.1 --port 18081 --alias haiku-qwen17 --reasoning off -n 128 > "$H/llama-server.log" 2>&1 &
model_pid=$!
ready=0
for attempt in $(seq 1 150); do
 kill -0 "$model_pid" 2>/dev/null || { echo 'Model exited during startup.' >&2; exit 1; }
 if curl -fsS --max-time 3 http://127.0.0.1:18081/health >/dev/null; then ready=1; break; fi
 sleep 2
done
[ "$ready" -eq 1 ] || { echo 'Model readiness deadline expired.' >&2; exit 1; }
cd /boot/home/opencode-work
export LIBRARY_PATH=/boot/system/lib
nohup "$OC/opencode" serve --hostname 127.0.0.1 --port 18083 > /boot/home/opencode-serve.log 2>&1 &
backend_pid=$!
ready=0
for attempt in $(seq 1 60); do
 kill -0 "$backend_pid" 2>/dev/null || { echo 'Backend exited during startup.' >&2; exit 1; }
 if curl -fsS --max-time 3 -u "opencode:$OPENCODE_PASSWORD" http://127.0.0.1:18083/api/info >/dev/null; then ready=1; break; fi
 sleep 2
done
[ "$ready" -eq 1 ] || { echo 'Backend readiness deadline expired.' >&2; exit 1; }
printf '%s\n' "$model_pid" > "$H/llama-server.pid"
printf '%s\n' "$backend_pid" > /boot/home/opencode-serve.pid
trap - EXIT HUP INT TERM
echo 'Model and shared OpenCode backend are ready; credentials preserved in /boot/home/opencode-env.sh.'
