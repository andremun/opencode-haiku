# Managing the cloud API key

Rules: the key lives in **one file outside the repository**, never in chat, Git, `share/`, `logs/`,
`results/`, job scripts or the VM disk. Use a dedicated key with no credit (or a low spend cap),
revoke it after each session, and create a new one next time. Tasks sent to cloud models must be
synthetic (some free models may use prompts for training).

## One-time setup (you, in your own terminal)

```bash
mkdir -p ~/.config/opencode-haiku-test && chmod 700 ~/.config/opencode-haiku-test
read -rs -p "key: " K && printf 'OPENCODE_API_KEY=%s\n' "$K" > ~/.config/opencode-haiku-test/cloud.env \
  && chmod 600 ~/.config/opencode-haiku-test/cloud.env; unset K
sh tools/secrets/install-hook.sh        # local pre-commit secret scan (hooks are not tracked by Git)
```

Override the location with `OPENCODE_CLOUD_ENV_FILE`. The helpers refuse a file that is not owned by
you, not mode 600/400, inside the repository, or without an `OPENCODE_API_KEY=` line.

## Running tests

Host (official client or the Haiku.5 bundle):

```bash
tools/secrets/with-cloud-key.sh env OPENCODE_TEST_PORT_ROOT=$HOME/.local/bin/opencode \
  OPENCODE_CLOUD_MODEL=opencode/glm-5.3-flash-free node tests/acceptance/cloud-coding-task.mjs OUT_DIR
```

The wrapper exports `OPENCODE_API_KEY` and `OPENCODE_CLOUD_PASS_API_KEY=1` to that one command and
prints nothing about the key.

Haiku VM (the key goes host to guest memory, never to a file):

1. Host: `python3 tools/secrets/serve-key-once.py` prints `KEY_URL=http://10.0.2.2:PORT/TOKEN`.
   The URL is random and single use; the server exits after one fetch, five bad requests, or 180 s.
2. Guest job (the job script holds only the URL):
   `sh /boot/home/opencode-haiku-src/tests/acceptance/vm/with-cloud-key-guest.sh KEY_URL env OPENCODE_TEST_PORT_ROOT=... OPENCODE_CLOUD_MODEL=... node .../cloud-coding-task.mjs OUT_DIR`
   (copy `with-cloud-key-guest.sh` and the runner into the guest as in the cloud task report).
   Start the server immediately before submitting the job.

Haiku's `/tmp` is on the persistent disk and deleted files remain recoverable from a qcow2 image, so
the design avoids creating any guest file that contains the key.

## Guard rails

- `tests/acceptance/cloud-coding-task.mjs` refuses non-free models (ids not ending in `-free` and not
  `big-pickle`) unless `OPENCODE_CLOUD_ALLOW_PAID=1`. It redacts the key from every saved log.
- `tools/secrets/scan_secrets.py` finds key-shaped strings and prints only `file:line: rule`.
  Run it over the repo (`python3 tools/secrets/scan_secrets.py`) after every session; the pre-commit
  hook runs it on staged files (`--staged`). `.gitignore` excludes `*.env`.
- Host tests (`tests/unit/test_t7610_runners.py`) cover the wrapper (permission, location, no output),
  the one-shot server (one use, wrong token, expiry path), the guest wrapper, the scanner and the
  paid-model guard, all with a fake key built at run time.

## End of session

1. `python3 tools/secrets/scan_secrets.py` (expect no findings).
2. Revoke the key in the Console. Tell the agent only that a key was used and revoked.
3. Shut the VM down; stop the transfer service and the one-shot server if still running.

## Limits

The key is visible to any process of yours that can read the file or the environment of the running
test, and to the cloud client process itself. The scanner finds known shapes, not every secret. A key
pasted into chat is exposed in that transcript: revoke it.
