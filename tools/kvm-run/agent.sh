#!/bin/sh
# Guest sequential job agent; publish one complete result and retry uploads without rerunning jobs.
set -eu
H=http://10.0.2.2:18080
n=${1:-1}
case "$n" in ''|*[!0-9]*|0|0*) echo 'Starting job number must be a positive integer.' >&2; exit 2;; esac
work=$(mktemp -d /tmp/opencode-jobs.XXXXXX)
trap 'rm -rf "$work"' EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
while :; do
 if curl -fs --max-time 30 -o "$work/job.sh" "$H/job$n.sh"; then
  if sh "$work/job.sh" > "$work/job.out" 2>&1; then rc=0; else rc=$?; fi
  printf '\nexit=%s\n' "$rc" >> "$work/job.out"
  until curl -fsS --max-time 30 -o /dev/null -X PUT --data-binary @"$work/job.out" "$H/job$n.out"; do sleep 2; done
  n=$((n+1))
 else sleep 2; fi
done
