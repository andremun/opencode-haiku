#!/bin/sh
set -eu
work=/boot/home/opencode-acceptance
cd "$work"
curl -fsS http://10.0.2.2:18080/haiku-clipboard.cpp -o haiku-clipboard.cpp
curl -fsS http://10.0.2.2:18080/haiku-clipboard.cjs -o haiku-clipboard.cjs
g++ -O2 haiku-clipboard.cpp -lbe -o haiku-clipboard
curl -fsS -T haiku-clipboard http://10.0.2.2:18080/haiku-clipboard.bin
