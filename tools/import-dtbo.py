#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
from prebuilts import ROOT,dtbo,digest
data=Path(sys.argv[1]).read_bytes();dtbo(data)
p=ROOT/'prebuilt/manifest.json';pins=json.loads(p.read_text())
expected=pins['files']['dtbo.img']
if expected and digest(data)!=expected:raise SystemExit('DTBO differs from pinned Dipper upload')
(ROOT/'prebuilt/dtbo.img').write_bytes(data)
pins['files']['dtbo.img']=digest(data)
p.write_text(json.dumps(pins,indent=2)+'\n')
sha=ROOT/'PREBUILTS.sha256'
lines=[l for l in sha.read_text().splitlines() if not l.endswith('  prebuilt/dtbo.img')]
sha.write_text('\n'.join(lines)+f'\n{digest(data)}  prebuilt/dtbo.img\n')
print('Dipper DTBO validated/imported; no flash operation')
