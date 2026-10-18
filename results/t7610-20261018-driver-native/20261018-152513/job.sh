#!/bin/sh
set -eu
host=http://10.0.2.2:34317
uname -a > /tmp/k40-environment.txt
curl -fsS -T /tmp/k40-environment.txt "$host/environment.txt"
curl -fsS -T /boot/system/kernel_x86_64 "$host/kernel_x86_64"
echo 0 > /tmp/k40-job.exit
curl -fsS -T /tmp/k40-job.exit "$host/job.exit"
