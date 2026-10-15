#!/usr/bin/env python3
"""Stage committed source and a verified runtime for a manual, non-SSH Haiku handoff."""
from pathlib import Path
import hashlib,json,subprocess,shutil
root=Path(__file__).resolve().parents[1]
share=root/'share';share.mkdir(exist_ok=True)
paths=['tools','reference','examples','docs','README.md','AGENTS.md']
dirty=subprocess.run(['git','diff','--quiet','HEAD','--',*paths],cwd=root).returncode
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',*paths],cwd=root,text=True).strip()
if dirty or untracked:raise SystemExit('Commit code, pins and instructions before staging. Generated results may remain unstaged.')
manifest=json.loads((root/'results/opencode-tui-package.json').read_text())
name=manifest['archive']
if Path(name).name!=name:raise SystemExit('Invalid archive name')
runtime=share/name
if hashlib.sha256(runtime.read_bytes()).hexdigest()!=manifest['sha256']:raise SystemExit('Rebuild the runtime: archive does not match package manifest')
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
source=share/'repo-next.tar.gz'
subprocess.run(['git','archive','--format=tar.gz','--output='+str(source),revision],cwd=root,check=True)
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
for file in ['persistent-terminal-api.mjs','api-workflow.mjs','legacy-pty-api.mjs','coding-workflow.mjs','inference-compare.cjs']:
 shutil.copyfile(root/'tools/tui-port'/file,share/file)
shutil.copyfile(root/'tools/kvm-run/agent.sh',share/'agent.sh')
script='''#!/bin/sh
set -eu
cd /tmp
curl -fsS --max-time 120 http://10.0.2.2:18080/repo-next.tar.gz -o repo-next.tar.gz
printf '%s\\n' 'SOURCE_HASH  repo-next.tar.gz' | sha256sum -c -
SRC=/boot/home/opencode-haiku-src
mkdir -p "$SRC"
tar -xzf repo-next.tar.gz -C "$SRC"
DEST=${OPENCODE_INSTALL_DEST:-/boot/home/opencode-haiku-2.0.29-haiku.5}
sh "$SRC/tools/tui-port/deploy_guest.sh" 'ARCHIVE_NAME' 'RUNTIME_HASH' "$DEST"
echo 'Committed source installed: SOURCE_REVISION'
echo "Runtime installed: $DEST"
'''.replace('SOURCE_HASH',source_hash).replace('ARCHIVE_NAME',name).replace('RUNTIME_HASH',manifest['sha256']).replace('SOURCE_REVISION',revision)
(share/'next-step.sh').write_text(script)
record={'source_commit':revision,'source_archive':source.name,'source_sha256':source_hash,'runtime_archive':name,'runtime_sha256':manifest['sha256']}
(share/'next-step.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
print('Start the host transfer service, then in Haiku: curl -fsS http://10.0.2.2:18080/next-step.sh -o /tmp/next; sh /tmp/next')
print('Only committed source is staged. Run after committing/pulling the desired changes. Existing install destinations are preserved.')
