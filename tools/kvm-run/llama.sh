#!/bin/sh
set -eu
# Guest: fetch repo, patch + build llama.cpp CPU baseline per T7610 guide sections 4-5.
set -x
mkdir -p /boot/home/opencode-haiku-src /boot/home/haiku-llm
cd /boot/home/opencode-haiku-src && curl -fsS http://10.0.2.2:18080/opencode-haiku-src.tar.gz | tar -xzf -
cd /boot/home/haiku-llm
[ -f llama-source.tar.gz ] || curl -fL --retry 3 https://codeload.github.com/ggml-org/llama.cpp/tar.gz/cf8b0dbda9ac0eac30ee33f87bc6702ead1c4664 -o llama-source.tar.gz
echo '6980c77f4ad311bca845848f5b899d1a68b35dec94de849ca1b2ce4bc3ca0a3a  llama-source.tar.gz' | sha256sum -c || exit 1
rm -rf llama llama.cpp-*; tar -xzf llama-source.tar.gz; mv llama.cpp-cf8b0dbda9ac0eac30ee33f87bc6702ead1c4664 llama
cd llama; PORT=/boot/home/opencode-haiku-src
for p in kepler-sm35-ggml-cuda reasoning-budget-rearm haiku-portability; do git apply --check $PORT/reference/llama-cpu/$p.patch && git apply $PORT/reference/llama-cpu/$p.patch || exit 2; done
cd ..
date
cmake -S llama -B build -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=OFF -DGGML_SSE42=OFF -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_BMI2=OFF -DGGML_FMA=OFF -DGGML_F16C=OFF -DGGML_CUDA=OFF -DGGML_OPENMP=OFF -DLLAMA_OPENSSL=OFF -DLLAMA_BUILD_WEBUI=OFF -DLLAMA_BUILD_TESTS=ON || exit 3
cmake --build build --parallel 2 --target llama-cli llama-completion llama-server test-reasoning-budget test-chat-template || exit 4
date
export LIBRARY_PATH=/boot/home/haiku-llm/build/bin:/boot/system/lib
./build/bin/test-reasoning-budget; echo test-reasoning-budget=$?
./build/bin/test-chat-template; echo test-chat-template=$?
./build/bin/llama-server --version
echo LLAMA-BUILD-DONE
