#!/bin/sh
# Cardless Haiku runtime prerequisite check; no model or service connection.
set -u
mkdir -p /boot/home/opencode-port
cd /boot/home/opencode-port || exit 1
(
    uname -a
    pkgman install -y nodejs24
    command -v node
    node --version
    node -p 'JSON.stringify({platform:process.platform,arch:process.arch,versions:process.versions})'
    curl -fS -o runtime-probe.mjs http://10.0.2.2:18080/opencode-runtime-probe.mjs
    node runtime-probe.mjs
) > runtime-probe.log 2>&1
rc=$?
printf '%s\n' "$rc" > runtime-probe.exit
curl -fS -T runtime-probe.log http://10.0.2.2:18080/opencode-guest-runtime.log
curl -fS -T runtime-probe.exit http://10.0.2.2:18080/opencode-guest-runtime.exit
exit "$rc"
