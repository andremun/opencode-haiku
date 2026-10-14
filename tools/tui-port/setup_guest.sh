#!/bin/sh
set -eu
work=/boot/home/opencode-acceptance
mkdir -p "$work"
cd "$work"
exec > setup.log 2>&1
upload() { curl -fsS -T setup.log http://10.0.2.2:18080/opencode-tui-setup.log || true; }
trap upload 0 1 2 15
pkgman install -y nodejs24_devel libffi_devel
whoami
id
# Export only development headers/libs to an ignored cross-build SDK archive.
tar -chzf haiku-sdk.tar.gz -C /boot/system/develop headers lib
curl -fsS -T haiku-sdk.tar.gz http://10.0.2.2:18080/opencode-haiku-sdk.tar.gz
curl -fsS http://10.0.2.2:18080/opencode-koffi.tgz -o koffi.tgz
mkdir -p koffi
tar -xzf koffi.tgz -C koffi
# Download the pinned model in the background; independent of SDK/FFI work.
(curl -fsS --max-time 600 http://10.0.2.2:18080/opencode-qwen17.gguf -o qwen17.gguf && echo '72c5c3cb38fa32d5256e2fe30d03e7a64c6c79e668ad84057e3bd66e250b24fb  qwen17.gguf' | sha256sum -c > model-check.log) > model-download.log 2>&1 &
printf '%s\n' "$!" > model-download.pid
upload
