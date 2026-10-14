#!/bin/sh
set -eu
work=/boot/home/opencode-acceptance
cd "$work"
mkdir -p final-port
curl -fsS --max-time 120 http://10.0.2.2:18080/opencode-haiku-tui-2.0.29-haiku.2.tar.gz -o tui.tar.gz
printf '%s\n' 'ea12569b53eab9c175e4afe6597ff7f1d35ce25419e21014660c83660ef5220d  tui.tar.gz' | sha256sum -c
 tar -xzf tui.tar.gz -C final-port
mkdir -p fixture state/data state/config state/cache state/state
curl -fsS http://10.0.2.2:18080/opencode-tui-config.json -o fixture/opencode.json
cd final-port
./opencode --version
