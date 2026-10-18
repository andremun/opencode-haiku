#!/bin/sh
set -eu
host=http://10.0.2.2:37329
uname -a > /tmp/k40-environment.txt
curl -fsS -T /tmp/k40-environment.txt "$host/environment.txt"
curl -fsS -T /boot/system/kernel_x86_64 "$host/kernel_x86_64"
base=/boot/system/non-packaged/add-ons/kernel/drivers
mkdir -p "$base/bin" "$base/dev/misc"
curl -fsS -o "$base/bin/k40_cardless_probe" "$host/probe"
chmod +x "$base/bin/k40_cardless_probe"
ln -sf ../../bin/k40_cardless_probe "$base/dev/misc/k40_cardless_probe"
echo K40-CARDLESS-BEGIN > /dev/dprintf
ls /dev/misc >/dev/null
sleep 3
echo K40-CARDLESS-END > /dev/dprintf
echo 0 > /tmp/k40-job.exit
curl -fsS -T /tmp/k40-job.exit "$host/job.exit"
