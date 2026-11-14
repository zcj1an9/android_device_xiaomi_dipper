#!/usr/bin/env python3
import json
from prebuilts import ROOT,dtbo,digest
pins=json.loads((ROOT/'prebuilt/manifest.json').read_text())
if pins['device']!='dipper' or not pins['files']['dtbo.img']:
    raise SystemExit('Dipper DTBO upload pending: run tools/import-dtbo.py first')
data=(ROOT/'prebuilt/dtbo.img').read_bytes();dtbo(data)
if digest(data)!=pins['files']['dtbo.img']:raise SystemExit('Dipper DTBO checksum mismatch')
print('Dipper embedded DTBO verified')
