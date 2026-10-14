#!/bin/sh
# Rebuild the tested full Node TUI/browser bundle from pinned cached sources.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
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
sh "$root/tools/tui-port/build_native.sh"
cd "$opentui"
"$bun" install --frozen-lockfile --ignore-scripts
cd packages/core
"$bun" scripts/build.ts --lib
cd "$opencode"
"$bun" install --frozen-lockfile --ignore-scripts
if ! patch --dry-run --reverse -p1 < "$root/reference/opencode-haiku-headless.patch" >/dev/null 2>&1; then
    patch -p1 < "$root/reference/opencode-haiku-headless.patch"
fi
python3 - "$opentui" "$opencode" <<'PY'
from pathlib import Path
import sys,shutil
opentui,opencode=map(Path,sys.argv[1:])
candidates=list(opencode.glob('node_modules/.bun/@opentui+core@0.5.17+*/node_modules/@opentui/core'))
if len(candidates)!=1:raise SystemExit('Expected exactly one pinned OpenTUI core dependency')
shutil.copytree(opentui/'packages/core/dist',candidates[0],dirs_exist_ok=True)
PY
OPENCODE_VERSION=2.0.29-haiku.2 OPENCODE_CHANNEL=haiku "$bun" packages/cli/script/build-node.ts --bundle-only --skip-install
cd "$root"
python3 tools/tui-port/package.py
