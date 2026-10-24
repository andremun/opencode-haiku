#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python3 - "$root" <<'PY'
from pathlib import Path
import json,sys,hashlib
root=Path(sys.argv[1]);data=json.loads((root/'reference/PTY-PORT-INPUTS.json').read_text())
for entry in data['inputs']:
 if entry['path'] in ['cache/ghostty-ab0b9da.tar.gz','patches/ghostty/ghostty-haiku-static.patch']:
  assert hashlib.sha256((root/entry['path']).read_bytes()).hexdigest()==entry['sha256'],entry['path']
PY
source="$root/source/ghostty-ab0b9da9e88fcb4b0533a1854e84628f663930af"
export PATH="$root/cache/build-tools/zig-x86_64-linux-0.16.0:$PATH"
cd "$source"
if ! patch --dry-run --reverse -p1 < "$root/patches/ghostty/ghostty-haiku-static.patch" >/dev/null 2>&1; then
 patch -p1 < "$root/patches/ghostty/ghostty-haiku-static.patch"
fi
zig build -Demit-lib-vt=true -Demit-xcframework=false -Dapp-runtime=none -Dtarget=x86_64-haiku -Dsimd=false -Doptimize=ReleaseFast --global-cache-dir "$root/cache/zig" --prefix "$root/cache/ghostty-haiku"
sha256sum "$root/cache/ghostty-haiku/lib/libghostty-vt.a"
