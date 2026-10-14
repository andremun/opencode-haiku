#!/bin/sh
# Run from any directory. No sudo; caches and extracted sources are ignored by Git.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$root"
revision=34d8ded0c58dd66808c1d60e081e8c66da12a896
source_dir="$root/source/opencode-$revision"
bun_dir="$root/cache/build-tools/bun-1.4.2"
bun="$bun_dir/bun-linux-x64/bun"
mkdir -p cache source logs share
if test ! -f cache/opencode-34d8ded0.tar.gz; then
    curl -fL --max-time 120 "https://codeload.github.com/anomalyco/opencode/tar.gz/$revision" -o cache/opencode-34d8ded0.tar.gz
fi
if test ! -f cache/bun-linux-x64-1.4.2.zip; then
    curl -fL --max-time 120 https://github.com/oven-sh/bun/releases/download/bun-v1.4.2/bun-linux-x64.zip -o cache/bun-linux-x64-1.4.2.zip
fi
printf '%s\n' \
 'bc76cf4bbd70e13027b21e56454364c20bbe183fed2f80ba57f4be1ebe573e59  cache/opencode-34d8ded0.tar.gz' \
 '36368faef7527875d5ffa52e53cd48021741f2a83eb6208a8dd64068d422a913  cache/bun-linux-x64-1.4.2.zip' | sha256sum -c
python3 - <<'PY'
from pathlib import Path
import tarfile,zipfile
source=Path('source/opencode-34d8ded0c58dd66808c1d60e081e8c66da12a896')
if not source.exists():
    with tarfile.open('cache/opencode-34d8ded0.tar.gz') as archive:archive.extractall('source',filter='data')
bun=Path('cache/build-tools/bun-1.4.2/bun-linux-x64/bun')
if not bun.exists():
    with zipfile.ZipFile('cache/bun-linux-x64-1.4.2.zip') as archive:archive.extractall(bun.parents[1])
    bun.chmod(0o755)
PY
if ! patch --dry-run --reverse -d "$source_dir" -p1 < reference/opencode-haiku-headless.patch > /dev/null 2>&1; then
    patch -d "$source_dir" -p1 < reference/opencode-haiku-headless.patch
fi
cd "$source_dir"
"$bun" install --frozen-lockfile --ignore-scripts > "$root/logs/opencode-install-rebuild.log" 2>&1
OPENCODE_VERSION=2.0.29-haiku.1 OPENCODE_CHANNEL=haiku "$bun" packages/cli/script/build-node.ts --bundle-only --skip-install > "$root/logs/opencode-port-rebuild.log" 2>&1
cd "$root"
python3 tools/opencode-port/package.py
