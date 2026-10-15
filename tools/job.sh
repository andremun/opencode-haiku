#!/bin/sh
# Usage: tools/job.sh FRESH_NUMBER 'shell commands' [wait_timeout_s]
# A wait timeout does not cancel the guest job. The result's final line carries its status.
set -eu
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then echo 'Usage: tools/job.sh N COMMANDS [TIMEOUT]' >&2; exit 2; fi
R=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
N=$1
T=${3:-300}
for value in "$N" "$T"; do
 case "$value" in ''|*[!0-9]*|0|0*) echo 'Job number and timeout must be canonical positive integers.' >&2; exit 2;; esac
done
mkdir -p "$R/share" "$R/logs"
request=$R/share/job$N.sh
result=$R/logs/job$N.out
if [ -e "$request" ] || [ -e "$result" ]; then echo 'Job number already used; choose a fresh number.' >&2; exit 2; fi
pending=$(mktemp "$R/share/.job$N.XXXXXX")
trap 'rm -f "$pending"' EXIT HUP INT TERM
printf '%s\n' "$2" > "$pending"
mv "$pending" "$request"
i=0
while [ ! -f "$result" ]; do
 if [ "$i" -ge "$T" ]; then echo 'TIMEOUT waiting for result; guest execution has not been cancelled.' >&2; exit 124; fi
 sleep 1
 i=$((i+1))
done
cat "$result"
last=$(tail -n 1 "$result")
case "$last" in exit=*) rc=${last#exit=};; *) echo 'Missing guest exit status.' >&2; exit 125;; esac
case "$rc" in ''|*[!0-9]*) echo 'Invalid guest exit status.' >&2; exit 125;; esac
if [ "$rc" -gt 255 ]; then echo 'Invalid guest exit status.' >&2; exit 125; fi
exit "$rc"
