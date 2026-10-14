#!/bin/sh
# Install a checksum-verified archive into a new user-owned directory.
set -eu
if test "$#" -ne 3; then echo 'Usage: install.sh ARCHIVE SHA256 NEW_DESTINATION' >&2; exit 2; fi
archive=$1
expected=$2
destination=$3
test -f "$archive"
if test -e "$destination"; then echo 'Choose a new destination; existing installations are preserved.' >&2; exit 1; fi
actual=$(sha256sum "$archive" | awk '{print $1}')
if test "$actual" != "$expected"; then echo 'Archive checksum mismatch.' >&2; exit 1; fi
case "$(node -p 'process.platform')" in haiku) ;; *) echo 'This runtime requires Haiku.' >&2; exit 1;; esac
node -e 'if(+process.versions.node.split(".")[0]<24)process.exit(1)'
mkdir -p "$destination"
trap 'rm -rf "$destination"' EXIT HUP INT TERM
tar -xzf "$archive" -C "$destination"
"$destination/opencode" --version
trap - EXIT HUP INT TERM
printf 'Installed in %s\nStart a shared backend: %s/opencode serve --hostname 127.0.0.1 --port 18083\nAttach TUI from your project: %s/opencode --server http://127.0.0.1:18083\n' "$destination" "$destination" "$destination"
