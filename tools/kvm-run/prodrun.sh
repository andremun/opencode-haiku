#!/bin/sh
# usage: prodrun.sh PROFILE  (guest) services + direct inference + 8-step coding, then stop owned services
p=$1
SRC=/boot/home/opencode-haiku-src
OC=/boot/home/opencode-haiku-2.0.29-haiku.5
. /boot/home/opencode-env.sh
cd /boot/home
OPENCODE_PORT_ROOT=$OC OPENCODE_LLAMA_PROFILE=$p OPENCODE_LLAMA_BATCH=512 OPENCODE_LLAMA_UBATCH=128 sh $SRC/tools/kvm-run/services.sh > /boot/home/services-$p.log 2>&1
echo "services rc=$?"; cat /boot/home/services-$p.log
cd /tmp
node $SRC/tools/tui-port/inference-compare.cjs http://127.0.0.1:18081 /boot/home/inference-$p.json jobinf-$p.json; echo "inference rc=$?"
mkdir -p /boot/home/coding-$p
OPENCODE_TEST_PORT_ROOT=$OC/opencode OPENCODE_TEST_STEPS=8 node $SRC/tools/tui-port/coding-workflow.mjs /boot/home/coding-$p > /boot/home/coding-$p/run.log 2>&1; echo "coding rc=$?"
cat /boot/home/coding-$p/coding-outcome.json
kill $(cat /boot/home/opencode-serve.pid) $(cat /boot/home/haiku-llm/llama-server.pid) 2>&1; echo stopped
