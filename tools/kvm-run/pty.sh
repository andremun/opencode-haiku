#!/bin/sh
# Native full logs and real statuses: never pipe a verifier into tail.
set -eu
W=${OPENCODE_NATIVE_WORK:-/boot/home/native-build}
cd "${OPENCODE_PTY_SOURCE:-$W/pty}"
unset LIBRARY_PATH
export CARGO_HOME="$W/cargo-cache" CARGO_TARGET_DIR="$W/cargo-target" OPENCODE_HAIKU_GHOSTTY_LIB="$W/pty-lib" CARGO_INCREMENTAL=0
date
cargo build --locked --jobs 1
cargo test --locked --jobs 1 -- --test-threads=1 > "$W/pty-tests-full.log" 2>&1 || { rc=$?; cat "$W/pty-tests-full.log"; exit "$rc"; }
cat "$W/pty-tests-full.log"
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings > "$W/pty-clippy-full.log" 2>&1 || { rc=$?; cat "$W/pty-clippy-full.log"; exit "$rc"; }
cat "$W/pty-clippy-full.log"
cp "$CARGO_TARGET_DIR/debug/opencode-pty" "$W/opencode-pty-bin"
strip --strip-debug "$W/opencode-pty-bin"
ls -l "$W/opencode-pty-bin"
sha256sum "$W/opencode-pty-bin"
rustc --version --verbose
echo PTY-DONE
