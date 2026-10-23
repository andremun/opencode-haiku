# Examples

| Path | What it is | Used by |
|---|---|---|
| `haiku-local-chat.json` | OpenCode configuration for a first inference test on Haiku. It points to a local llama.cpp server at `http://127.0.0.1:18081/v1` (model alias `haiku-qwen17`, Qwen3 1.7B on the CPU). All tools are denied. Replies are limited to 64 tokens. | [docs/INSTALL.md](../docs/INSTALL.md), step 9. `tests/acceptance/vm/services.sh` starts a matching server. |
| `cloud-task/start/` | Synthetic coding task: a CSV parser and a report function with two test files. The functions throw "not implemented". | `tests/acceptance/cloud-coding-task.mjs` (acceptance check M-02) copies it into a new fixture folder for each run. |
| `cloud-task/reference/src/` | A reference solution of the task. The agent never sees it. | The host tests `tests/unit/test_review_runners.py` and `tests/unit/test_t7610_runners.py` use it to check the runners. |

## Use the local chat configuration

1. Start a llama.cpp server on port 18081 with the alias `haiku-qwen17`.
2. Copy the file as `opencode.json` into an empty work folder.
3. Start OpenCode in that folder.

For another endpoint or model, change `baseURL`, the model key and the `model` fields.
Keep `apiKey` empty in the file. Give keys through the methods in
[docs/SECRETS.md](../docs/SECRETS.md).

## Rules for the cloud task

- The task is synthetic. Do not replace it with private code. Some free cloud models
  can use prompts for training ([docs/SECRETS.md](../docs/SECRETS.md)).
- Do not change the files in `cloud-task/start/test/`. The acceptance check compares
  their hashes before and after the run.
- A change of the task needs a change of the reference solution and a new run of the
  host tests.
