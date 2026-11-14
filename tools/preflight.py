#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from prebuilts import ROOT, verify

p=argparse.ArgumentParser()
p.add_argument('--source-only',action='store_true',help='Check source layout without claiming binaries are ready')
a=p.parse_args()
profile=json.loads((ROOT/'device-profile.json').read_text())
device=profile['device']
board=(ROOT/'BoardConfig.mk').read_text()
with tempfile.TemporaryDirectory() as tmp:
    target=Path(tmp)/'device/xiaomi'/device;target.parent.mkdir(parents=True)
    target.symlink_to(ROOT,target_is_directory=True)
    result=subprocess.run(['make','--no-print-directory','-f','-'],cwd=tmp,input=f'''include device/xiaomi/{device}/BoardConfig.mk
all:
\t@echo $(TARGET_PREBUILT_KERNEL) $(BOARD_PREBUILT_DTBOIMAGE) $(BOARD_INCLUDE_RECOVERY_DTBO) $(BOARD_MKBOOTIMG_ARGS)
''',text=True,capture_output=True,check=True).stdout.strip()
    expected=f'device/xiaomi/{device}/prebuilt/Image.gz-dtb device/xiaomi/{device}/prebuilt/dtbo.img true --header_version 1 --ramdisk_offset 0x01000000 --tags_offset 0x00000100'
    if result!=expected:raise SystemExit('Unexpected expanded Make kernel/DTBO arguments: '+result)
wf=(ROOT/'.github/workflows/build-recovery.yml').read_text()
if '  push:' in wf or 'strategy:' in wf or 'matrix.' in wf:
    raise SystemExit('Workflow must be manual-only and single-device')
if f"refs/heads/twrp-16.0-{device}" not in wf:
    raise SystemExit('Workflow must guard its device branch')
if f'PRODUCT_DEVICE := {device}' not in (ROOT/f'twrp_{device}.mk').read_text():
    raise SystemExit('Product mismatch')
fstab=(ROOT/'recovery/recovery.fstab').read_text()
flags=(ROOT/'recovery/root/system/etc/twrp.flags').read_text()
for line in flags.splitlines():
    fields=line.split()
    if len(fields)>1 and fields[1]=='emmc' and ('canbewiped=0' not in line or 'wipeingui=0' not in line):
        raise SystemExit('Raw image exposed to Advanced Wipe: '+fields[0])
for part,mount in profile['mounts']:
    for fs in ['ext4','erofs']:
        if f'{part} {mount} {fs} ' not in fstab:
            raise SystemExit('Missing filesystem/mount mapping')
if '/dev/block/mapper/' in fstab or '/by-name/super' in fstab:
    raise SystemExit('Unverified logical layout')
for path in ['BoardConfig.mk','device.mk','tools/build.sh','tools/sync-source.sh']:
    if 'device/xiaomi/dipper' in (ROOT/path).read_text():
        raise SystemExit('Dipper hardware path leaked into independent tree')
if not a.source_only:verify()
print(device+': source checks passed'+('; binary upload and hardware test pending' if a.source_only else '; both prebuilts verified'))
