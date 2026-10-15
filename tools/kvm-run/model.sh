mkdir -p /boot/home/haiku-llm/models; cd /boot/home/haiku-llm/models
curl -fL --retry 3 --continue-at - https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/dcb19155b962dbb6389f4691a982043a8e651022/Qwen_Qwen3-1.7B-Q4_K_M.gguf -o Qwen3-1.7B-Q4_K_M.gguf
echo '72c5c3cb38fa32d5256e2fe30d03e7a64c6c79e668ad84057e3bd66e250b24fb  Qwen3-1.7B-Q4_K_M.gguf' | sha256sum -c; wc -c Qwen3-1.7B-Q4_K_M.gguf
echo MODEL-DONE
