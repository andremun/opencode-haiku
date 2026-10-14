#!/bin/sh
set -eu
work=/boot/home/opencode-acceptance
cd "$work"
mkdir -p final-port
curl -fsS --max-time 120 http://10.0.2.2:18080/opencode-haiku-tui-2.0.29-haiku.3.tar.gz -o tui.tar.gz
printf '%s\n' '21f1861f8906f5f76f2e9ad1ec72fa47d3d1e1cf0d6b98493ed7f93ef7a9293e  tui.tar.gz' | sha256sum -c
 tar -xzf tui.tar.gz -C final-port
mkdir -p fixture state/data state/config state/cache state/state
curl -fsS http://10.0.2.2:18080/opencode-tui-config.json -o fixture/opencode.json
cd final-port
./opencode --version
