#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$root/share/http-test"
cp -R "$root/source/opencode-34d8ded0c58dd66808c1d60e081e8c66da12a896/node_modules/.bun/undici@7.29.0/node_modules/undici" "$root/share/http-test/"
cp "$root/src/haiku-http.cjs" "$root/tests/unit/http-test.cjs" "$root/share/http-test/"
node "$root/share/http-test/http-test.cjs"
tar -czf "$root/share/http-test.tar.gz" -C "$root/share/http-test" .
"$root/cache/build-tools/bun-1.4.2/bun-linux-x64/bun" build "$root/tests/unit/clipboard-integrated.ts" --target=node --outfile "$root/share/clipboard-integrated.mjs"
