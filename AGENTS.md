# opencode-haiku

Read docs/STATUS.md first. This independent repository contains the native Haiku
headless OpenCode port, source pins, build tooling and measured evidence.
No dependency on the sibling Haiku LLM or llm-server repositories is required
to build or run OpenCode. A model endpoint is a separately selected service.

Use only a cardless VM. Never access, reset or pass through a physical GPU,
alter host drivers or running LLM services, or use host sudo. The user
explicitly authorises cardless Haiku VM work without host sudo. Do not start
subagents. Keep assumptions separate from measured evidence.

Read sibling AGENTS.md instructions before changing a sibling repository.
Keep source archives, dependency caches, models and virtual disks outside Git.
Record exact hashes, commands, failed and pending tests in docs/STATUS.md.
Do not push without instruction. A CPU/cardless result is not GPU evidence.
