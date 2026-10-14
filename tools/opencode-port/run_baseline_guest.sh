#!/bin/sh
set -u
mkdir -p /boot/home/opencode-port/baseline
cd /boot/home/opencode-port/baseline || exit 1
export XDG_DATA_HOME=/boot/home/opencode-port/state/data
export XDG_CONFIG_HOME=/boot/home/opencode-port/state/config
export XDG_CACHE_HOME=/boot/home/opencode-port/state/cache
export XDG_STATE_HOME=/boot/home/opencode-port/state/state
(
    set -e
    curl -fS -o baseline.tar.gz http://10.0.2.2:18080/opencode-node-baseline.tar.gz
    tar -xzf baseline.tar.gz
    node opencode.mjs --help
    node opencode.mjs --version
) > baseline.log 2>&1
rc=$?
printf '%s\n' "$rc" > baseline.exit
curl -fS -T baseline.log http://10.0.2.2:18080/opencode-guest-baseline.log
curl -fS -T baseline.exit http://10.0.2.2:18080/opencode-guest-baseline.exit
exit "$rc"
