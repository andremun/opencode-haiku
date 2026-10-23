#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Conservative native CPU profile for TCG and tool prompts.
set -eu
work=/boot/home/opencode-acceptance
cd "$work"
if curl -fsS --max-time 2 http://127.0.0.1:18081/health >/dev/null 2>&1; then
 echo 'Model endpoint already owned; refusing a duplicate server.' >&2; exit 1
fi
export LIBRARY_PATH=/boot/home/haiku-app/build/bin:/boot/system/lib
/boot/home/haiku-app/build/bin/llama-server -m qwen17.gguf -ngl 0 -t 2 -tb 2 -b 128 -ub 32 -c 4096 --parallel 1 --poll 0 --poll-batch 0 --cache-ram 128 --host 127.0.0.1 --port 18081 --alias haiku-qwen17 --reasoning off -n 128 > llama-server-small-batch.log 2>&1 &
printf '%s\n' "$!" > llama-server-small-batch.pid
ready=0
attempt=0
while test "$attempt" -lt 90; do
 attempt=$((attempt+1))
 if curl -fsS --max-time 5 http://127.0.0.1:18081/health; then ready=1;break;fi
 sleep 2
done
test "$ready" = 1
