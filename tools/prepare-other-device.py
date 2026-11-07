#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare isolated hardware bring-up trees from the tested dipper core tooling."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'aee2411485463c7f3389a40caf95f7404ef2b240'


def git_head(root):
    return subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()


def setvar(text, name, value):
    pattern = r'^' + re.escape(name) + r'\s*:=.*$'
    if re.search(pattern, text, re.M):
        return re.sub(pattern, f'{name} := {value}', text, flags=re.M)
    return text + f'\n{name} := {value}\n'


def prepare_board(device, profile, board):
    board = board.replace('dipper', device)
    values = {
        'BOARD_BOOT_HEADER_VERSION': profile['boot_header'],
        'BOARD_BOOTIMG_HEADER_VERSION': profile['boot_header'],
        # AOSP checks this with ifdef; even the string false enables it.
        'BOARD_INCLUDE_RECOVERY_DTBO': '',
        'BOARD_MKBOOTIMG_ARGS': '--header_version 0 --ramdisk_offset 0x01000000 --tags_offset 0x00000100',
        'TARGET_OTA_ASSERT_DEVICE': device,
        'TW_MAX_BRIGHTNESS': profile['brightness'],
        'TW_DEFAULT_BRIGHTNESS': profile['default_brightness'],
        'TW_Y_OFFSET': profile['y_offset'], 'TW_H_OFFSET': profile['h_offset'],
    }
    board = re.sub(r'^BOARD_MKBOOTIMG_ARGS\s*\+=.*\n', '', board, flags=re.M)
    for key, value in values.items():
        board = setvar(board, key, value)
    # Keep device DTBOs in their separate partition, not in header-v0 recovery.
    if device == 'equuleus':
        board += 'LZMA_RAMDISK_TARGETS := recovery\n'
    return board


def prepare(device, base, hardware, target, built_kernel, kernel_meta):
    profiles = json.loads((ROOT / 'devices/bringup-targets.json').read_text())
    profile = profiles[device]
    provenance_kernel = json.loads(kernel_meta.read_text())
    kernel_bytes = built_kernel.read_bytes()
    # Read the first gzip member; appended DTBs are not gzip members.
    kernel_image = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(kernel_bytes)
    release = re.search(rb'Linux version (4[.]19[.][^ \x00]+)', kernel_image)
    if (profile.get('kernel_version') != '4.19' or not release
            or provenance_kernel.get('device') != device
            or provenance_kernel.get('commit') != profile['kernel_commit']
            or provenance_kernel.get('sha256') != hashlib.sha256(kernel_bytes).hexdigest()):
        raise ValueError('A source-built device-specific 4.19 kernel is required')
    if git_head(base) != BASE_COMMIT or git_head(hardware) != profile['commit']:
        raise ValueError('Source checkout does not match pinned provenance')
    if target.exists():
        raise ValueError('Output must be a new directory')
    for relative, expected in profile['blobs'].items():
        data = (hardware / relative).read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != expected:
            raise ValueError(f'Pinned hardware blob mismatch: {relative}')
    shutil.copytree(base, target, ignore=shutil.ignore_patterns('.git', '__pycache__'))
    # Shared source paths and log filenames become device-specific. DIPPER_*
    # environment names remain the existing CI tool interface, not hardware IDs.
    for path in list(target.rglob('*')):
        if path.is_file():
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            if 'dipper' in text:
                path.write_text(text.replace('dipper', device))
    for path in sorted(target.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if 'dipper' in path.name:
            path.rename(path.with_name(path.name.replace('dipper', device)))
    board = prepare_board(device, profile, (target / 'BoardConfig.mk').read_text())
    (target / 'BoardConfig.mk').write_text(board)
    p = target / 'device.mk'
    p.write_text(setvar(p.read_text(), 'TARGET_SCREEN_HEIGHT', profile['screen_height']))
    p = target / f'twrp_{device}.mk'
    p.write_text(setvar(p.read_text(), 'PRODUCT_MODEL', profile['model']))
    kernel = target / 'prebuilt/Image.gz-dtb'
    kernel.parent.mkdir(exist_ok=True)
    shutil.copy2(built_kernel, kernel)
    usb = target / 'recovery/root/init.recovery.usb.rc'
    shutil.copy2(hardware / 'recovery/root/init.recovery.usb.rc', usb)
    # First build excludes userdata and vendor crypto HALs. Its filesystem and
    # key policy have not been supplied for either installed ROM.
    (target / 'crypto-profile.mk').write_text('''TW_USE_FSCRYPT_POLICY := 2
TW_INCLUDE_CRYPTO := false
TW_INCLUDE_CRYPTO_FBE := false
TW_INCLUDE_FBE_METADATA_DECRYPT := false
BOARD_USES_METADATA_PARTITION := false
''')
    (target / 'crypto-profile.json').write_text(json.dumps({
        'mode': 'bringup', 'device': device, 'data_mount': False,
        'hardware_crypto_services': False, 'device_tested': False,
    }, indent=2) + '\n')
    (target / 'tools/ci-configure.py').write_text('''#!/usr/bin/env python3
import json
from pathlib import Path
r = Path(__file__).resolve().parents[1]
p = json.loads((r / 'crypto-profile.json').read_text())
assert p['mode'] == 'bringup' and p['data_mount'] is False
print('Hardware bring-up profile checked; userdata excluded')
''')
    (target / 'tools/fetch-prebuilts.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
(cd "$package_dir" && sha256sum -c PREBUILTS.sha256)
''')
    root = target / 'recovery/root'
    (root / 'init.recovery.qcom.rc').write_text('''# Hardware bring-up only: no installed vendor services or partition writes.
on fs
    wait /dev/block/platform/soc/${ro.boot.bootdevice} 5
    symlink /dev/block/platform/soc/${ro.boot.bootdevice} /dev/block/bootdevice

on boot
    setprop sys.usb.config adb
''')
    for path in ['fstab.qcom', 'vendor/etc/fstab.qcom']:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text('# No userdata or guessed crypto profile in bring-up mode.\n')
    (root / 'vendor/etc/vintf').mkdir(parents=True, exist_ok=True)
    (root / 'system/etc').mkdir(parents=True, exist_ok=True)
    (root / 'vendor/etc/vintf/manifest.xml').write_text('<manifest version="1.0" type="device" />\n')
    # Partition devices and filesystem types are derived from this device's
    # upstream fstab, not the dipper layout. Only cache is writable for settings.
    source_fstab = (hardware / profile['fstab']).read_text()
    fstab, flags = [], []
    approved = {'/cache', '/system', '/system_root', '/vendor', '/cust', '/persist', '/firmware'}
    for line in source_fstab.splitlines():
        fields = line.split()
        if len(fields) < 3 or fields[0] not in approved:
            continue
        mount, fs, block = fields[:3]
        if fs not in {'ext4', 'vfat'} or not block.startswith('/dev/block/bootdevice/by-name/'):
            raise ValueError('Unexpected upstream mount contract')
        opts = 'noatime,nosuid,nodev' if mount == '/cache' else ('ro,noload' if fs == 'ext4' else 'ro')
        fstab.append(f'{block} {mount} {fs} {opts} wait,recoveryonly')
        flags.append(f'{mount} {fs} {block} flags=backup=1;canbewiped=0;wipeingui=0')
    if not any(' /cache ' in line for line in fstab):
        raise ValueError('Upstream cache mount required for settings persistence')
    fstab.append('/dev/block/bootdevice/by-name/misc /misc emmc defaults defaults')
    (target / 'recovery/recovery.fstab').write_text('\n'.join(fstab) + '\n')
    (root / 'system/etc/twrp.flags').write_text('\n'.join(flags) + '\n')
    provenance = dict(profile, shared_tree_commit=BASE_COMMIT, mode='bringup',
                      dtbo_partition_modified=False, hardware_tested=False,
                      built_kernel=provenance_kernel)
    (target / 'DEVICE_PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    shutil.copy2(hardware / 'BoardConfig.mk', target / 'UPSTREAM-BoardConfig.mk.reference')
    shutil.copy2(hardware / profile['fstab'], target / 'UPSTREAM-fstab.reference')
    # Verify actual binary bytes in addition to the pinned Git blobs above.
    (target / 'PREBUILTS.sha256').write_text(''.join(
        hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(target)) + '\n'
        for p in [kernel, usb]))
    (target / 'README.md').write_text(f'''# TWRP hardware bring-up: {device}

Generated from tested shared tree {BASE_COMMIT} and {profile['repository']} at {profile['commit']}.
Source-built 4.19 kernel, display/brightness and USB init are specific to {device}.
Data mounting/decryption and destructive partition actions are excluded in this first hardware test.
Existing phone DTBO is retained. Perseus's appended DTBs are SoC base trees; its external device DTBO must match this kernel. No DTBO is packaged or flashed.
Full build and hardware behavior are pending; this is not a verified Android 17 decrypting recovery.
After a successful temporary boot, verify touch, display, battery, USB/ADB and cache settings persistence before extending userdata support.
See DEVICE_PROVENANCE.json and UPSTREAM-*.reference for hardware input provenance.
''')
    print(json.dumps(provenance, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device', choices=['equuleus', 'perseus'], required=True)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--hardware', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--kernel', type=Path, required=True)
    p.add_argument('--kernel-meta', type=Path, required=True)
    a = p.parse_args()
    prepare(a.device, a.base.resolve(), a.hardware.resolve(), a.output.resolve(),
            a.kernel.resolve(), a.kernel_meta.resolve())
