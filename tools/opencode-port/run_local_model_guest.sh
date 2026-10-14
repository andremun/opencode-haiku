#!/bin/sh
set -u
cd /boot/home/opencode-port/port || exit 1
export XDG_DATA_HOME=/boot/home/opencode-port/state/data
export XDG_CONFIG_HOME=/boot/home/opencode-port/state/config
export XDG_CACHE_HOME=/boot/home/opencode-port/state/cache
export XDG_STATE_HOME=/boot/home/opencode-port/state/state
curl -fsS http://10.0.2.2:18080/opencode-port.mjs -o opencode.mjs || exit 1
curl -fsS http://10.0.2.2:18080/opencode-local-model-probe.mjs -o local_model_probe.mjs || exit 1
node local_model_probe.mjs . > local-model-runner.log 2>&1
rc=$?
curl -fsS -T local-model.log http://10.0.2.2:18080/opencode-guest-local-model.log
curl -fsS -T local-model.exit http://10.0.2.2:18080/opencode-guest-local-model.exit
exit "$rc"
