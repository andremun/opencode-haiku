#!/bin/sh
set -u
work=/boot/home/opencode-acceptance
cd "$work" || exit 1
(
 set -e
 curl -fsS http://10.0.2.2:18080/opencode-koffi-source.tar.gz -o koffi-source.tar.gz
 tar -xzf koffi-source.tar.gz
 gcc -print-file-name=include
 g++ -print-file-name=libstdc++.so
 g++ -E -x c++ /dev/null -v
 gcc_lib_dir=$(dirname "$(gcc -print-file-name=libgcc.a)")
 (cd "$gcc_lib_dir" && tar -chzf "$work/gcc-sdk.tar.gz" include libgcc* libstdc++* crt*.o)
 curl -fsS -T gcc-sdk.tar.gz http://10.0.2.2:18080/opencode-haiku-gcc-sdk.tar.gz
 cd koffi
 node cnoke.cjs clean -P . -D src/koffi --release
 MAKEFLAGS=-j2 node cnoke.cjs -P . -D src/koffi --release
) > ffi-build.log 2>&1
rc=$?
printf '%s\n' "$rc" > ffi-build.exit
curl -fsS -T ffi-build.log http://10.0.2.2:18080/opencode-tui-ffi-build.log
curl -fsS -T ffi-build.exit http://10.0.2.2:18080/opencode-tui-ffi-build.exit
exit "$rc"
