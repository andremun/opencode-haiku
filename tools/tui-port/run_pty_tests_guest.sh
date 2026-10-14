#!/bin/sh
set -u
work=/boot/home/opencode-acceptance
export CARGO_HOME="$work/cargo-cache"
export CARGO_TARGET_DIR="$work/cargo-target"
export OPENCODE_HAIKU_GHOSTTY_LIB="$work/pty-lib"
unset LIBRARY_PATH
cd "$work/pty-source" || exit 1
cargo test --locked --jobs 1 -- --test-threads=1 > "$work/pty-native-tests.log" 2>&1
rc=$?
echo "$rc" > "$work/pty-native-tests.exit"
curl -fsS --max-time 10 -T "$work/pty-native-tests.log" http://10.0.2.2:18080/pty-native-tests.log
curl -fsS --max-time 10 -T "$work/pty-native-tests.exit" http://10.0.2.2:18080/pty-native-tests.exit
exit "$rc"
