#!/usr/bin/env python3
"""Package the headless Node bundle, assets and upstream MIT license."""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source/opencode-34d8ded0c58dd66808c1d60e081e8c66da12a896'
DIST=SOURCE/'packages/cli/dist-node'
output=ROOT/'share/opencode-haiku-headless-2.0.29-haiku.1.tar.gz'
with tarfile.open(output,'w:gz') as archive:
    for path,name in [(DIST/'opencode.mjs','opencode.mjs'),(DIST/'assets','assets'),(SOURCE/'LICENSE','LICENSE'),(ROOT/'tools/opencode-port/opencode','opencode')]:
        archive.add(path,arcname=name)
manifest={'archive':output.name,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bundle_sha256':hashlib.sha256((DIST/'opencode.mjs').read_bytes()).hexdigest()}
(ROOT/'results/opencode-package.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest))
