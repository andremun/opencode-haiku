#!/bin/sh
# Guest job runner: fetch jobN.sh from the localhost transfer service, run it, upload jobN.out.
H=http://10.0.2.2:18080
n=${1:-1}
while :; do
  if curl -sf -o /tmp/job.sh $H/job$n.sh; then
    sh /tmp/job.sh > /tmp/job.out 2>&1
    echo "exit=$?" >> /tmp/job.out
    curl -s -X PUT --data-binary @/tmp/job.out $H/job$n.out
    n=$((n+1))
  else sleep 2; fi
done
