#!/usr/bin/env python3
"""Exercise install success, checksum rejection and preservation on failure."""
from pathlib import Path
import subprocess,tempfile,tarfile,hashlib,os
script=Path(__file__).with_name('install.sh').resolve()
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp); mock=root/'bin';mock.mkdir()
 node=mock/'node';node.write_text('#!/bin/sh\nif test "$1" = -p; then echo haiku; fi\n');node.chmod(0o755)
 source=root/'opencode';source.write_text('#!/bin/sh\necho TEST_VERSION\n');source.chmod(0o755)
 archive=root/'fixture.tar.gz'
 with tarfile.open(archive,'w:gz') as tar:tar.add(source,arcname='opencode')
 checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
 env={**os.environ,'PATH':str(mock)+':'+os.environ['PATH']}
 def run(hash,destination):return subprocess.run(['sh',str(script),str(archive),hash,str(destination)],env=env,capture_output=True,text=True)
 destination=root/'new installation'
 assert run('0'*64,destination).returncode!=0 and not destination.exists()
 assert run(checksum,destination).returncode==0 and (destination/'opencode').exists()
 sentinel=destination/'keep';sentinel.write_text('preserve')
 assert run(checksum,destination).returncode!=0 and sentinel.read_text()=='preserve'
 source.write_text('#!/bin/sh\nexit 7\n')
 with tarfile.open(archive,'w:gz') as tar:tar.add(source,arcname='opencode')
 checksum=hashlib.sha256(archive.read_bytes()).hexdigest();failed=root/'failed'
 assert run(checksum,failed).returncode!=0 and not failed.exists()
 print('INSTALL_TEST_PASS: checksum, success, existing preservation, partial cleanup')
