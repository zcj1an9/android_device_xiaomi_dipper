#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import json
import struct
import sys
from pathlib import Path
from prebuilts import ROOT, verify

verify()
b=Path(sys.argv[1]).read_bytes()
if b[:8]!=b'ANDROID!' or not 1648<len(b)<=67108864:raise SystemExit('Invalid image size/magic')
ks=struct.unpack_from('<I',b,8)[0]
rs=struct.unpack_from('<I',b,16)[0]
page,hv=struct.unpack_from('<II',b,36)
ds,offset,header=struct.unpack_from('<IQI',b,1632)
if (page,hv,header)!=(4096,1,1648):raise SystemExit('Wrong recovery header layout')
align=lambda n:(n+page-1)//page*page
if offset!=page+align(ks)+align(rs) or offset+ds>len(b):raise SystemExit('Wrong DTBO offset')
if b[page:page+ks]!=(ROOT/'prebuilt/Image.gz-dtb').read_bytes():raise SystemExit('Kernel changed')
if b[offset:offset+ds]!=(ROOT/'prebuilt/dtbo.img').read_bytes():raise SystemExit('DTBO changed')
profile=json.loads((ROOT/'device-profile.json').read_text())
if profile['device']=='perseus' and b[-64:-60]!=b'AVBf':raise SystemExit('Missing reference-style AVB footer')
print('Built recovery contains the exact per-device kernel and DTBO; hardware boot remains to be tested')
