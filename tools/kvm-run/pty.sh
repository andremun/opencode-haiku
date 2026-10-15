W=/boot/home/native-build; cd $W/pty
unset LIBRARY_PATH; export CARGO_HOME=$W/cargo-cache CARGO_TARGET_DIR=$W/cargo-target OPENCODE_HAIKU_GHOSTTY_LIB=$W/pty-lib CARGO_INCREMENTAL=0
date; cargo build --locked --jobs 1; echo build=$?; date
cargo test --locked --jobs 1 -- --test-threads=1 2>&1 | tail -12; echo test-done
cargo fmt --all -- --check; echo fmt=$?
cargo clippy --all-targets --all-features -- -D warnings 2>&1 | tail -5; echo clippy=$?
cp $CARGO_TARGET_DIR/debug/opencode-pty $W/opencode-pty-bin && strip --strip-debug $W/opencode-pty-bin; ls -l $W/opencode-pty-bin; sha256sum $W/opencode-pty-bin; rustc --version --verbose | head -3
echo PTY-DONE
