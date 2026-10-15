#!/bin/sh
# Cold means a fresh server with no smoke inference before the measured requests.
set -eu
H=${OPENCODE_LLAMA_WORK:-/boot/home/haiku-llm}
cd "$H"
mkdir -p inf
curl -fsS --max-time 60 http://10.0.2.2:18080/inference-compare.cjs -o inf/inference-compare.cjs
export LIBRARY_PATH="$H/build/bin:/boot/system/lib"
pid=
stop() {
 if [ -n "$pid" ]; then
  kill "$pid" 2>/dev/null || true
  n=0
  while kill -0 "$pid" 2>/dev/null && [ "$n" -lt 30 ]; do n=$((n+1)); sleep 1; done
  kill -KILL "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  pid=
 fi
}
trap stop EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
start() {
 if curl -s --max-time 2 -o /dev/null http://127.0.0.1:18081/health; then echo 'Refusing to benchmark an existing model endpoint.' >&2; exit 1; fi
 t0=$(date +%s)
 ./build/bin/llama-server -m models/Qwen3-1.7B-Q4_K_M.gguf -ngl 0 -t 2 -tb 2 -b 128 -ub 32 -c 4096 --parallel 1 --poll 0 --poll-batch 0 --cache-ram 128 --host 127.0.0.1 --port 18081 --alias haiku-qwen17 --reasoning off -n 128 > "inf/llama-server-$1.log" 2>&1 &
 pid=$!
 printf '%s\n' "$pid" > inf/pid
 n=0
 while [ "$n" -lt 300 ]; do
  kill -0 "$pid" 2>/dev/null || { echo 'Owned model server exited during startup.' >&2; exit 1; }
  if curl -fsS --max-time 3 http://127.0.0.1:18081/health >/dev/null; then echo "$1 ready after $(( $(date +%s) - t0 )) s"; return; fi
  n=$((n+1)); sleep 2
 done
 echo 'Model readiness deadline expired.' >&2
 exit 1
}
run() { t=$(date +%s); node inf/inference-compare.cjs http://127.0.0.1:18081 "inf/$1.json" "jobinf-$1.json"; echo "$1 wall $(( $(date +%s) - t )) s"; }
upload() { curl -fsS --max-time 30 -o /dev/null -X PUT --data-binary @"inf/llama-server-$1.log" "http://10.0.2.2:18080/jobinf-server-$1.log"; }
printf '%s\n' './build/bin/llama-server -m models/Qwen3-1.7B-Q4_K_M.gguf -ngl 0 -t 2 -tb 2 -b 128 -ub 32 -c 4096 --parallel 1 --poll 0 --poll-batch 0 --cache-ram 128 --host 127.0.0.1 --port 18081 --alias haiku-qwen17 --reasoning off -n 128' > inf/server-command.txt
start cold1
run cold1
run warm1
stop
upload cold1
start cold2
run cold2
stop
upload cold2
echo INF-DONE
