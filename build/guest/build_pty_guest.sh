#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -eu
work=/boot/home/opencode-acceptance
cd "$work"
curl -fsS --max-time 60 http://10.0.2.2:18080/opencode-pty-haiku-source.tar.gz -o pty-source.tar.gz
curl -fsS --max-time 60 http://10.0.2.2:18080/libghostty-vt.a -o libghostty-vt.a
# Accept the original pin or the 2026-10-15 rebuild (reference/PTY-PORT-INPUTS.json records both).
sum=$(sha256sum libghostty-vt.a | cut -d' ' -f1)
case "$sum" in 44fd3d15ae62e94315a0ee6aa91b77994a42cb0649573a1d6d42c208e029f2f2|9182565a75720c8273a1be632b1d421dab754b812fdba68fcdece8df9f2e23e5) ;; *) echo "libghostty-vt.a checksum mismatch: $sum" >&2; exit 1;; esac
printf '%s  %s\n' '420249f1d13d71b7bafff4aaef1e8a1aa72978ea6194f9abcc6ac34eafb2c38b' pty-source.tar.gz | sha256sum -c -
mkdir -p pty-source pty-lib
tar -xzf pty-source.tar.gz -C pty-source
mv libghostty-vt.a pty-lib/
export CARGO_HOME="$work/cargo-cache"
export CARGO_TARGET_DIR="$work/cargo-target"
export OPENCODE_HAIKU_GHOSTTY_LIB="$work/pty-lib"
unset LIBRARY_PATH
cd pty-source
set +e
cargo check --locked --jobs 1 > "$work/pty-cargo-check.log" 2>&1
rc=$?
set -e
printf '%s\n' "$rc" > "$work/pty-cargo-check.exit"
curl -fsS --max-time 10 -T "$work/pty-cargo-check.log" http://10.0.2.2:18080/pty-cargo-check.log
curl -fsS --max-time 10 -T "$work/pty-cargo-check.exit" http://10.0.2.2:18080/pty-cargo-check.exit
exit "$rc"
