. /boot/home/opencode-env.sh
curl -fsS -X POST -u "opencode:$OPENCODE_PASSWORD" http://127.0.0.1:18083/api/pair -o /boot/home/pair.json
node -e 'const fs=require("node:fs");const r=JSON.parse(fs.readFileSync("/boot/home/pair.json","utf8"));const code=r.code??r.data?.code;if(!code)throw Error("Missing pairing code");console.log("http://127.0.0.1:18083/auth/connect/"+code)' > /boot/home/pair-link.txt
echo ok
