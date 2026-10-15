W=/boot/home/opencode-acceptance; OC=/boot/home/opencode-haiku-2.0.29-haiku.4
mkdir -p $W/t; cd $W/t
for f in api-workflow.mjs legacy-pty-api.mjs persistent-terminal-api.mjs; do curl -fsS http://10.0.2.2:18080/$f -o $f; done
rm -rf $W/http-port-dir $W/http-port; ln -sfn $OC $W/http-port; ln -sfn $OC/node-pty $W/node-pty
export LIBRARY_PATH=/boot/system/lib
echo "### api-workflow (files, shell, session persistence)"; date
node api-workflow.mjs $W; echo "exit=$?"; cat $W/api-probe.log | tail -c 1500; echo
echo "### legacy browser PTY (node-pty binding)"; date
node legacy-pty-api.mjs $W; echo "exit=$?"; tail -c 2500 $W/api-probe.log; echo
echo "### persistent daemon terminals"; date
node persistent-terminal-api.mjs $W $OC/opencode > $W/persistent-terminal-api.jsonl 2>&1; cat $W/persistent-terminal-api.jsonl; curl -s -X PUT --data-binary @$W/persistent-terminal-api.jsonl http://10.0.2.2:18080/jobapi-persistent-terminal.jsonl; echo "exit=$?"; date
echo API-TESTS-DONE
curl -s -X PUT --data-binary @/boot/home/api-tests-final.log http://10.0.2.2:18080/jobapi-final.log
