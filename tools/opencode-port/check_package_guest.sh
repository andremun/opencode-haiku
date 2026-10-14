#!/bin/sh
set -u
work=/boot/home/opencode-port/package-check
mkdir -p "$work"
cd "$work" || exit 1
export XDG_DATA_HOME=/boot/home/opencode-port/package-state/data
export XDG_CONFIG_HOME=/boot/home/opencode-port/package-state/config
export XDG_CACHE_HOME=/boot/home/opencode-port/package-state/cache
export XDG_STATE_HOME=/boot/home/opencode-port/package-state/state
(
 set -e
 pkgman install -y ripgrep
 rg --version
 curl -fsS http://10.0.2.2:18080/opencode-haiku-headless-2.0.29-haiku.1.tar.gz -o package.tar.gz
 echo '84831c3e3f21273100dab2b58953608c47e8d2e340a208fa61893f36d3b5aaac  package.tar.gz' | sha256sum -c
 tar -xzf package.tar.gz
 ./opencode --help
 ./opencode --version
 curl -fsS http://10.0.2.2:18080/opencode-api-probe.mjs -o api_probe.mjs
 node api_probe.mjs .
) > package-check.log 2>&1
rc=$?
printf '%s\n' "$rc" > package-check.exit
curl -fsS -T package-check.log http://10.0.2.2:18080/opencode-guest-package-check.log
curl -fsS -T package-check.exit http://10.0.2.2:18080/opencode-guest-package-check.exit
if test -f api-probe.log; then curl -fsS -T api-probe.log http://10.0.2.2:18080/opencode-guest-package-api.log; fi
exit "$rc"
