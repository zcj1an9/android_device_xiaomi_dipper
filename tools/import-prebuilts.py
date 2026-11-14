#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import argparse
import json
from pathlib import Path
from prebuilts import ROOT, digest, validate_pair

p=argparse.ArgumentParser(description='Import only the current device kernel/DTBO pair; never downloads or flashes.')
p.add_argument('--kernel',type=Path,required=True)
p.add_argument('--dtbo',type=Path,required=True)
a=p.parse_args()
pins=json.loads((ROOT/'prebuilt/manifest.json').read_text())
k,d=a.kernel.read_bytes(),a.dtbo.read_bytes()
validate_pair(k,d,pins)
# Validate both before changing any destination. Existing pinned hashes are retained.
for name,data in [('Image.gz-dtb',k),('dtbo.img',d)]:
    pins['files'][name]=digest(data)
    (ROOT/'prebuilt'/name).write_bytes(data)
(ROOT/'prebuilt/manifest.json').write_text(json.dumps(pins,indent=2)+'\n')
(ROOT/'PREBUILTS.sha256').write_text(''.join(f'{pins["files"][name]}  prebuilt/{name}\n' for name in ('Image.gz-dtb','dtbo.img')))
print(f'Validated/imported {pins["device"]} kernel and embedded recovery DTBO; no partition was flashed')
