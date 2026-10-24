#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Rebuild the tested full Node TUI/browser bundle from pinned cached sources.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
bun_dir="$root/cache/build-tools/bun-1.4.2/bun-linux-x64"
bun="$bun_dir/bun"
export PATH="$bun_dir:$PATH"
if test ! -e "$bun_dir/bunx"; then ln -s bun "$bun_dir/bunx"; fi
opentui="$root/source/opentui-6f0efd3330978d696b42db3d7d95d2042008312b"
opencode="$root/source/opencode-34d8ded0c58dd66808c1d60e081e8c66da12a896"
if test ! -d "$opentui" || test ! -d "$opencode"; then
    echo 'Extract the pinned source archives recorded in reference/TUI-PORT-INPUTS.json first.' >&2
    exit 1
fi
sh "$root/build/build_native.sh"
cd "$opentui"
"$bun" install --frozen-lockfile --ignore-scripts
if ! patch --dry-run --reverse -p1 < "$root/patches/opentui/opentui-haiku-clipboard.patch" >/dev/null 2>&1; then
    patch -p1 < "$root/patches/opentui/opentui-haiku-clipboard.patch"
fi
cd packages/core
"$bun" scripts/build.ts --lib
cd "$opencode"
"$bun" install --frozen-lockfile --ignore-scripts
# Restore only the three pinned files touched by overlapping OpenCode patches.
# This source checkout is an ignored build input, not a user working repository.
python3 - "$root" "$opencode" <<'RESTORE'
from pathlib import Path
import tarfile,sys,hashlib
root,source=map(Path,sys.argv[1:]);archive=root/'cache/opencode-34d8ded0.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='bc76cf4bbd70e13027b21e56454364c20bbe183fed2f80ba57f4be1ebe573e59'
with tarfile.open(archive) as tar:
 prefix=tar.getnames()[0].split('/')[0]
 for relative in ['packages/core/src/pty/pty.node.ts','packages/core/src/persistent-pty/binary.node.ts','packages/cli/vite.node.config.ts']:
  (source/relative).write_bytes(tar.extractfile(prefix+'/'+relative).read())
RESTORE
patch --batch -p1 < "$root/patches/opencode/opencode-haiku-headless.patch"
patch --batch -p1 < "$root/patches/opencode/opencode-haiku-terminals.patch"
python3 - "$opentui" "$opencode" <<'PY'
from pathlib import Path
import sys,shutil
opentui,opencode=map(Path,sys.argv[1:])
candidates=list(opencode.glob('node_modules/.bun/@opentui+core@0.5.17+*/node_modules/@opentui/core'))
if len(candidates)!=1:raise SystemExit('Expected exactly one pinned OpenTUI core dependency')
shutil.copytree(opentui/'packages/core/dist',candidates[0],dirs_exist_ok=True)
PY
OPENCODE_VERSION=$(cat "$root/VERSION") OPENCODE_CHANNEL=haiku "$bun" packages/cli/script/build-node.ts --bundle-only --skip-install
cd "$root"
python3 build/package.py
