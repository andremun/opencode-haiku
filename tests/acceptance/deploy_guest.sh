#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Haiku: fetch a named archive and install with the repository's checksum installer.
set -eu
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
 echo 'Usage: deploy_guest.sh ARCHIVE SHA256 NEW_DESTINATION [TRANSFER_BASE_URL]' >&2; exit 2
fi
archive=$1
expected=$2
destination=$3
base=${4:-http://10.0.2.2:18080}
case "$archive" in */*|'') echo 'ARCHIVE must be a basename.' >&2; exit 2;; esac
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
work=$(mktemp -d /tmp/opencode-install.XXXXXX)
trap 'rm -rf "$work"' EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
curl -fsS --max-time 600 "$base/$archive" -o "$work/runtime.tar.gz"
sh "$here/install.sh" "$work/runtime.tar.gz" "$expected" "$destination"
