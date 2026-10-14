#!/bin/sh
set -u
mkdir -p /boot/home/opencode-port/port
cd /boot/home/opencode-port/port || exit 1
export XDG_DATA_HOME=/boot/home/opencode-port/state/data
export XDG_CONFIG_HOME=/boot/home/opencode-port/state/config
export XDG_CACHE_HOME=/boot/home/opencode-port/state/cache
export XDG_STATE_HOME=/boot/home/opencode-port/state/state
(
    set -e
    curl -fS -o port.tar.gz http://10.0.2.2:18080/opencode-node-port.tar.gz
    tar -xzf port.tar.gz
    node opencode.mjs --help
    node opencode.mjs --version
) > port.log 2>&1
rc=$?
printf '%s\n' "$rc" > port.exit
curl -fS -T port.log http://10.0.2.2:18080/opencode-guest-port.log
curl -fS -T port.exit http://10.0.2.2:18080/opencode-guest-port.exit
exit "$rc"
