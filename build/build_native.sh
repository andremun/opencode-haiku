#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
python3 - <<'PY'
from pathlib import Path
import json,hashlib
m=json.loads(Path('reference/TUI-PORT-INPUTS.json').read_text())
verified=[]
for row in m['inputs']:
 if row['path'].startswith('cache/') or row['path'].endswith('.patch'):
  p=Path(row['path']);actual=hashlib.sha256(p.read_bytes()).hexdigest()
  allowed={row['sha256'],row.get('previous_sha256')}
  if actual not in allowed:raise SystemExit('Checksum mismatch: '+str(p))
  verified.append({'path':str(p),'sha256':actual,'bytes':p.stat().st_size,'record':'current' if actual==row['sha256'] else 'previous documented build'})
Path('results/native-build-inputs.json').write_text(json.dumps(verified,indent=2)+'\n')
PY

zig_dir="$root/cache/build-tools/zig-x86_64-linux-0.16.0"
source_dir="$root/source/opentui-6f0efd3330978d696b42db3d7d95d2042008312b"
apply_patch() {
 if ! patch --dry-run --reverse -d "$1" -p1 < "$2" >/dev/null 2>&1; then patch -d "$1" -p1 < "$2"; fi
}
apply_patch "$zig_dir" "$root/reference/zig-haiku-io.patch"
apply_patch "$source_dir" "$root/reference/opentui-haiku-native.patch"
apply_patch "$source_dir" "$root/reference/opentui-haiku-js.patch"
apply_patch "$source_dir" "$root/reference/opentui-haiku-ghostty-vt.patch"
cd "$source_dir/packages/native"
sh scripts/prepare-zig-deps.sh
export OPENTUI_HAIKU_SDK="$root/cache/haiku-sdk"
export OPENTUI_HAIKU_LIBC="$root/cache/haiku-libc.txt"
export ZIG_GLOBAL_CACHE_DIR="$root/cache/zig"
"$zig_dir/zig" build -Dlibrary-target=x86_64-haiku -Dtarget=x86_64-haiku -Doptimize=ReleaseFast
