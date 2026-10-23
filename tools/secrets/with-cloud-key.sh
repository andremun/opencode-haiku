#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Run COMMAND with the cloud API key in its environment, without ever printing the key.
# Usage: tools/secrets/with-cloud-key.sh COMMAND [ARGS...]
# The key lives in a file OUTSIDE the repository, mode 600, owned by you:
#   ~/.config/opencode-haiku-test/cloud.env   (override with OPENCODE_CLOUD_ENV_FILE)
# containing one line:  OPENCODE_API_KEY=<key>      See docs/SECRETS.md.
set -eu
[ "$#" -ge 1 ] || { echo 'Usage: with-cloud-key.sh COMMAND [ARGS...]' >&2; exit 2; }
f=${OPENCODE_CLOUD_ENV_FILE:-$HOME/.config/opencode-haiku-test/cloud.env}
repo=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
[ -f "$f" ] || { echo "Key file not found: $f (see docs/SECRETS.md)" >&2; exit 2; }
[ -O "$f" ] || { echo 'Key file must be owned by you.' >&2; exit 2; }
mode=$(stat -c %a "$f")
case "$mode" in 600|400) ;; *) echo "Key file must be mode 600 or 400 (it is $mode)." >&2; exit 2;; esac
case "$(realpath "$f")" in "$repo"|"$repo"/*) echo 'Key file must be outside the repository.' >&2; exit 2;; esac
key=$(sed -n 's/^OPENCODE_API_KEY=//p' "$f" | head -n 1)
[ -n "$key" ] || { echo 'No OPENCODE_API_KEY= line in the key file.' >&2; exit 2; }
export OPENCODE_API_KEY="$key"
export OPENCODE_CLOUD_PASS_API_KEY=1
unset key
exec "$@"
