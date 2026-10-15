#!/bin/sh
# Guest native build stage: Koffi, clipboard, SDK export, node-pty, PTY daemon. Per T7610 guide section 10.
W=/boot/home/native-build; mkdir -p $W; cd $W
log(){ echo "=== $1 $(date)"; }
log fetch
curl -fsS http://10.0.2.2:18080/guest-stage.tar.gz -o stage.tar.gz && tar -xzf stage.tar.gz || exit 1
curl -fsS http://10.0.2.2:18080/libghostty-vt.a -o libghostty-vt.a
echo '9182565a75720c8273a1be632b1d421dab754b812fdba68fcdece8df9f2e23e5  libghostty-vt.a' | sha256sum -c || exit 2
mkdir -p pty-lib && mv libghostty-vt.a pty-lib/
log clipboard
g++ -O2 haiku-clipboard.cpp -lbe -o haiku-clipboard; echo clipboard=$?
log koffi
( cd koffi && node cnoke.cjs clean -P . -D src/koffi --release; MAKEFLAGS=-j2 node cnoke.cjs -P . -D src/koffi --release; echo koffi=$?; find build -name koffi.node )
log nodepty
mkdir -p node-pty/build/Release
g++ -std=c++17 -D_DEFAULT_SOURCE -O2 -fPIC -shared -pthread -DNAPI_VERSION=8 -I/boot/system/develop/headers/node -I$W/node-addon-api node-pty/src/unix/pty.cc -lbsd -o node-pty/build/Release/pty.node; echo nodepty=$?
log sdk
tar -chzf haiku-sdk.tar.gz -C /boot/system/develop headers lib; echo sdk=$?
gcc_lib_dir=$(dirname "$(gcc -print-file-name=libgcc.a)")
(cd "$gcc_lib_dir" && tar -chzf $W/gcc-sdk.tar.gz include libgcc* libstdc++* crt*.o); echo gccsdk=$?
ls -l *.tar.gz; sha256sum haiku-sdk.tar.gz gcc-sdk.tar.gz koffi/build/koffi/haiku_x64/koffi.node haiku-clipboard node-pty/build/Release/pty.node
log pty
( unset LIBRARY_PATH; export CARGO_HOME=$W/cargo-cache CARGO_TARGET_DIR=$W/cargo-target OPENCODE_HAIKU_GHOSTTY_LIB=$W/pty-lib CARGO_INCREMENTAL=0
  cd pty && cargo build --locked --jobs 1 && cargo test --locked --jobs 1 -- --test-threads=1 2>&1 | tail -15; echo pty-test=$? )
cp $W/cargo-target/debug/opencode-pty $W/opencode-pty-bin && strip --strip-debug $W/opencode-pty-bin; ls -l $W/opencode-pty-bin; sha256sum $W/opencode-pty-bin
log done
echo NATIVE-BUILD-DONE
