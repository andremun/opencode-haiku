#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -u
work=/boot/home/opencode-acceptance
export CARGO_HOME="$work/cargo-cache"
export CARGO_TARGET_DIR="$work/cargo-target"
export OPENCODE_HAIKU_GHOSTTY_LIB="$work/pty-lib"
export CARGO_INCREMENTAL=0
unset LIBRARY_PATH
cd "$work/pty-source" || exit 1
cargo clippy --locked --jobs 1 --all-targets --all-features -- -D warnings > "$work/pty-clippy.log" 2>&1
rc=$?
echo "$rc" > "$work/pty-clippy.exit"
curl -fsS --max-time 10 -T "$work/pty-clippy.log" http://10.0.2.2:18080/pty-clippy.log
curl -fsS --max-time 10 -T "$work/pty-clippy.exit" http://10.0.2.2:18080/pty-clippy.exit
exit "$rc"
