# Guest inference controls: cold (fresh server), warm (same server), cold repeat. T7610 guide s7 and s11.
H=/boot/home/haiku-llm; cd $H; mkdir -p inf
curl -fsS http://10.0.2.2:18080/inference-compare.cjs -o inf/inference-compare.cjs
export LIBRARY_PATH=$H/build/bin:/boot/system/lib
CMD="./build/bin/llama-server -m models/Qwen3-1.7B-Q4_K_M.gguf -ngl 0 -t 2 -tb 2 -b 128 -ub 32 -c 4096 --parallel 1 --poll 0 --poll-batch 0 --cache-ram 128 --host 127.0.0.1 --port 18081 --alias haiku-qwen17 --reasoning off -n 128"
echo "$CMD" > inf/server-command.txt
start(){ t0=$(date +%s); $CMD > inf/llama-server-$1.log 2>&1 & echo $! > inf/pid
  n=0; while [ $n -lt 300 ]; do curl -fsS --max-time 3 http://127.0.0.1:18081/health >/dev/null 2>&1 && break; n=$((n+1)); sleep 2; done
  echo "$1 server ready after $(( $(date +%s) - t0 )) s (health attempts $n)"; }
stop(){ kill $(cat inf/pid); sleep 5; }
run(){ t=$(date +%s); node inf/inference-compare.cjs http://127.0.0.1:18081 inf/$1.json jobinf-$1.json; echo "$1 wall $(( $(date +%s) - t )) s"; }
uptime
start cold1; curl -fsS http://127.0.0.1:18081/v1/models | head -c 300; echo
curl -fsS --max-time 1800 http://127.0.0.1:18081/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"haiku-qwen17","messages":[{"role":"user","content":"Reply with OK only."}],"temperature":0,"seed":1234,"max_tokens":64,"stream":false,"chat_template_kwargs":{"enable_thinking":false}}' -o inf/inference-ok.json; echo "smoke curl=$?"; curl -s -X PUT --data-binary @inf/inference-ok.json http://10.0.2.2:18080/jobinf-smoke.json
run cold1
run warm1
curl -s -X PUT --data-binary @inf/llama-server-cold1.log http://10.0.2.2:18080/jobinf-server-cold1.log
stop; start cold2; run cold2
curl -s -X PUT --data-binary @inf/llama-server-cold2.log http://10.0.2.2:18080/jobinf-server-cold2.log
stop; echo INF-DONE
