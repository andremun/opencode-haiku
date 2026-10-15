mkdir -p /boot/home/opencode-work /boot/home/opencode-profile/data /boot/home/opencode-profile/config /boot/home/opencode-profile/cache /boot/home/opencode-profile/state
cp /boot/home/opencode-haiku-src/examples/haiku-local-chat.json /boot/home/opencode-work/opencode.json
cat > /boot/home/opencode-env.sh <<'EE'
OC=/boot/home/opencode-haiku-2.0.29-haiku.4
export XDG_DATA_HOME=/boot/home/opencode-profile/data XDG_CONFIG_HOME=/boot/home/opencode-profile/config XDG_CACHE_HOME=/boot/home/opencode-profile/cache XDG_STATE_HOME=/boot/home/opencode-profile/state
export OPENCODE_PASSWORD='CHOOSE-A-LOCAL-TEST-PASSWORD'
cd /boot/home/opencode-work
EE
H=/boot/home/haiku-llm; cd $H; export LIBRARY_PATH=$H/build/bin:/boot/system/lib
nohup ./build/bin/llama-server -m models/Qwen3-1.7B-Q4_K_M.gguf -ngl 0 -t 2 -tb 2 -b 128 -ub 32 -c 4096 --parallel 1 --poll 0 --poll-batch 0 --cache-ram 128 --host 127.0.0.1 --port 18081 --alias haiku-qwen17 --reasoning off -n 128 > $H/llama-server.log 2>&1 &
sleep 20; curl -fsS http://127.0.0.1:18081/health; echo
. /boot/home/opencode-env.sh; export LIBRARY_PATH=/boot/system/lib
nohup $OC/opencode serve --hostname 127.0.0.1 --port 18083 > /boot/home/opencode-serve.log 2>&1 &
sleep 15; tail -3 /boot/home/opencode-serve.log; curl -s -u opencode:$OPENCODE_PASSWORD http://127.0.0.1:18083/api/info | head -c 300
