#!/bin/sh
set -u
work=/boot/home/opencode-acceptance
cd "$work" || exit 1
(
 set -e
 for name in haiku-ffi.cjs haiku-loader.cjs ffi-fixture.c ffi-test.cjs; do curl -fsS "http://10.0.2.2:18080/opencode-$name" -o "$name"; done
 gcc -shared -fPIC ffi-fixture.c -o ffi-fixture.so
 export OPENCODE_HAIKU_KOFFI="$work/koffi"
 node --require "$work/haiku-loader.cjs" ffi-test.cjs "$work/ffi-fixture.so"
 test -f model-check.log
 cat model-check.log
 export LIBRARY_PATH=/boot/home/haiku-app/build/bin
 /boot/home/haiku-app/build/bin/llama-server -m qwen17.gguf -ngl 0 -t 2 -c 4096 --parallel 1 --host 127.0.0.1 --port 18081 --alias haiku-qwen17 --reasoning off -n 128 > llama-server.log 2>&1 &
 printf '%s\n' "$!" > llama-server.pid
 ready=0
 for n in $(seq 1 180); do
  if curl -fsS --max-time 2 http://127.0.0.1:18081/health > health.json; then ready=1;break;fi
  sleep 1
 done
 test "$ready" = 1
 curl -fsS --max-time 600 -H 'Content-Type: application/json' --data '{"model":"haiku-qwen17","messages":[{"role":"user","content":"Reply with the single word OK."}],"max_tokens":16,"temperature":0,"chat_template_kwargs":{"enable_thinking":false}}' http://127.0.0.1:18081/v1/chat/completions > native-chat.json
 cat native-chat.json
) > native-check.log 2>&1
rc=$?
printf '%s\n' "$rc" > native-check.exit
for name in native-check.log native-check.exit llama-server.log native-chat.json; do if test -f "$name"; then curl -fsS -T "$name" "http://10.0.2.2:18080/opencode-tui-$name"; fi; done
exit "$rc"
