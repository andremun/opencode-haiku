#!/bin/sh
set -eu
W=/boot/home/opencode-acceptance; cd $W/t
curl -fsS http://10.0.2.2:18080/coding-workflow.mjs -o coding-workflow.mjs
export LIBRARY_PATH=/boot/system/lib
date > $W/coding-start.txt
if node coding-workflow.mjs "$W" > "$W/coding-stdout.log" 2>&1; then rc=0; else rc=$?; fi
echo "exit=$rc" >> "$W/coding-start.txt"
date >> "$W/coding-start.txt"
exit "$rc"
