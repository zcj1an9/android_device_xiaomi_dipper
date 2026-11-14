#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate an explicit per-device static layout without guessing FBE options."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BLOCK='/dev/block/bootdevice/by-name/'
p=argparse.ArgumentParser()
p.add_argument('--mode',choices=['storage','diagnostic'],default='storage')
a=p.parse_args()
profile=json.loads((ROOT/'device-profile.json').read_text())
mounts=profile['mounts']
fstab=[];flags=[]
def entry(part,mount,fs,opts):
    fstab.append(f'{BLOCK}{part} {mount} {fs} {opts} wait')
def flag(part,mount,fs,title,backup,wipe,extra=''):
    flags.append(f'{mount} {fs} {BLOCK}{part} flags=display="{title}";backup={backup};canbewiped={wipe};wipeingui={wipe}'+extra)
for part,mount in mounts:
    for fs,opts in [('ext4','ro,noload'),('erofs','ro')]:
        entry(part,mount,fs,opts)
    flag(part,mount,'ext4',mount[1:],0,1)
entry('cache','/cache','ext4','noatime,nosuid,nodev')
flag('cache','/cache','ext4','Cache',1,1,';settingsstorage')
for part,mount,fs,opts in [('persist','/persist','ext4','ro,noload'),('modem','/firmware','vfat','ro')]:
    entry(part,mount,fs,opts);flag(part,mount,fs,mount[1:],0,0)
if a.mode=='storage':
    for fs in ('ext4','f2fs'):
        entry('userdata','/data',fs,'noatime,nosuid,nodev')
    flag('userdata','/data','ext4','Data',1,1,';storage')
fstab.append(f'{BLOCK}misc /misc emmc defaults defaults')
images=[('boot','boot'),('recovery','recovery'),('dtbo','dtbo')]
images += [(mount[1:]+'_image',part) for part,mount in mounts]
images += [('persist_image','persist'),('modem','modem'),('bluetooth','bluetooth'),('dsp','dsp'),
           ('efs1','modemst1'),('efs2','modemst2'),('efsc','fsc'),('efsg','fsg'),('misc','misc')]
for mount,part in images:
    extra=';flashimg='+str(int(part not in {'modemst1','modemst2','fsc','fsg','misc'}))
    if mount in {'efs2','efsc','efsg'}:extra+=';subpartitionof=/efs1'
    flag(part,'/'+mount,'emmc',mount,1,0,extra)
flags.append('/usb_otg auto /dev/block/sdg1 /dev/block/sdg flags=display="USB-OTG";storage;removable;backup=0;canbewiped=1;wipeingui=1')
(ROOT/'recovery/recovery.fstab').write_text('\n'.join(fstab)+'\n')
etc=ROOT/'recovery/root/system/etc';etc.mkdir(parents=True,exist_ok=True)
(etc/'twrp.flags').write_text('\n'.join(flags)+'\n')
# Default fstab is restricted to the selected data mode. No key services are started.
for name in ['fstab.qcom','vendor/etc/fstab.qcom']:
    path=ROOT/'recovery/root'/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(line for line in fstab if ' /data ' in line)+'\n')
(ROOT/'crypto-profile.json').write_text(json.dumps({'mode':a.mode,'device':profile['device'],'data_mount':a.mode=='storage','hardware_crypto_services':False},indent=2)+'\n')
print(profile['device'],a.mode,'partition configuration ready')
