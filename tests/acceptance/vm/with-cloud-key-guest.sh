#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Haiku guest: fetch the API key from the host's one-shot server into memory and run COMMAND.
# Usage: with-cloud-key-guest.sh KEY_URL COMMAND [ARGS...]
# The key is never written to a file or echoed; the job script holds only the single-use URL.
set -eu
[ "$#" -ge 2 ] || { echo 'Usage: with-cloud-key-guest.sh KEY_URL COMMAND [ARGS...]' >&2; exit 2; }
url=$1; shift
key=$(curl -fsS --max-time 20 "$url") || { echo 'Could not fetch the key (one-shot server used up, expired or not running).' >&2; exit 2; }
[ -n "$key" ] || { echo 'Empty key.' >&2; exit 2; }
export OPENCODE_API_KEY="$key"
export OPENCODE_CLOUD_PASS_API_KEY=1
unset key
exec "$@"
