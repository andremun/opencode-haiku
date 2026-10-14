#!/usr/bin/env python3
from pathlib import Path
import tarfile,hashlib,json
root=Path(__file__).resolve().parents[2]
source=root/'source/opencode-34d8ded0c58dd66808c1d60e081e8c66da12a896'
dist=source/'packages/cli/dist-node'
native=root/'source/opentui-6f0efd3330978d696b42db3d7d95d2042008312b/packages/native/lib/x86_64-haiku/libopentui.so'
asset=dist/'assets/@opentui/core-haiku-x64/libopentui.so'
asset.parent.mkdir(parents=True,exist_ok=True)
import shutil
shutil.copy2(native,asset)
output=root/'share/opencode-haiku-tui-2.0.29-haiku.4.tar.gz'
addon=root/'cache/opencode-final-koffi.node'
if not addon.is_file():raise SystemExit('Export the final guest-built Koffi addon first')
temporary=output.with_suffix('.tmp')
with tarfile.open(temporary,'w:gz') as t:
 for p,name in [(dist/'opencode.mjs','opencode.mjs'),(dist/'assets','assets'),(source/'LICENSE','LICENSE')]:t.add(p,arcname=name)
 for name in ['opencode','haiku-loader.cjs','haiku-ffi.cjs','haiku-watch.cjs','haiku-clipboard.cjs','selftest.cjs','haiku-http.cjs']:t.add(root/'tools/tui-port'/name,arcname=name)
 def executable(info):
  info.mode=0o755
  return info
 t.add(root/'cache/haiku-clipboard',arcname='haiku-clipboard',filter=executable)
 t.add(root/'cache/pty-runtime/opencode-pty',arcname='opencode-pty',filter=executable)
 t.add(root/'cache/pty-runtime/node-pty',arcname='node-pty')
 t.add(source/'node_modules/.bun/undici@7.29.0/node_modules/undici',arcname='undici')
 koffi=root/'source/koffi-3.3.3/package'
 for name in ['index.cjs','package.json','src/koffi/index.cjs','src/koffi/src/static.cjs','LICENSE.txt']:
  t.add(koffi/name,arcname='koffi/'+name)
 t.add(root/'cache/opencode-final-koffi.node',arcname='koffi/build/koffi/haiku_x64/koffi.node')
 opentui=native.parents[4]
 t.add(opentui/'LICENSE',arcname='licenses/opentui/LICENSE')
 for base in [opentui/'packages/native/src/vendor',opentui/'packages/native/zig-deps']:
  for notice in sorted(base.rglob('*')):
   if notice.is_file() and notice.name.lower().split('.')[0] in {'license','copying','notice'}:
    t.add(notice,arcname='licenses/opentui/'+str(notice.relative_to(opentui)))
 for name in ['vendor/node-addon-api/LICENSE.md','vendor/node-api-headers/LICENSE']:
  t.add(koffi/name,arcname='licenses/koffi/'+name)
temporary.replace(output)
manifest={'archive':output.name,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bundle_sha256':hashlib.sha256((dist/'opencode.mjs').read_bytes()).hexdigest(),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'koffi_sha256':hashlib.sha256((root/'cache/opencode-final-koffi.node').read_bytes()).hexdigest(),'clipboard_sha256':hashlib.sha256((root/'cache/haiku-clipboard').read_bytes()).hexdigest(),'acceptance':'Haiku.2 TUI/GUI CPU baseline; Haiku.3 clipboard and installation checks recorded separately'}
(root/'results/opencode-tui-package.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest))
