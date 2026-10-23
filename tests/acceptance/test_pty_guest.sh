#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
set -u
work=/boot/home/opencode-acceptance
export CARGO_HOME="$work/cargo-cache"
export CARGO_TARGET_DIR="$work/cargo-target"
export OPENCODE_HAIKU_GHOSTTY_LIB="$work/pty-lib"
unset LIBRARY_PATH
cd "$work/pty-source" || exit 1
cargo fmt --check > "$work/pty-fmt.log" 2>&1
echo "$?" > "$work/pty-fmt.exit"
curl -fsS --max-time 10 -T "$work/pty-fmt.log" http://10.0.2.2:18080/pty-fmt.log
curl -fsS --max-time 10 -T "$work/pty-fmt.exit" http://10.0.2.2:18080/pty-fmt.exit
cargo test --locked --jobs 1 --no-run > "$work/pty-native-link.log" 2>&1
rc=$?
echo "$rc" > "$work/pty-native-link.exit"
curl -fsS --max-time 10 -T "$work/pty-native-link.log" http://10.0.2.2:18080/pty-native-link.log
curl -fsS --max-time 10 -T "$work/pty-native-link.exit" http://10.0.2.2:18080/pty-native-link.exit
exit "$rc"
