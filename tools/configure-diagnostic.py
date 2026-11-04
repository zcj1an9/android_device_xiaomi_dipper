#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate diagnostic or unencrypted storage mounts without hardware crypto HALs."""
import json
import argparse
from pathlib import Path
from partition_layout import extra_mounts, recovery_flags

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mount-data', action='store_true',
                    help='Storage mode for a confirmed unencrypted userdata filesystem')
args = parser.parse_args()
mode = 'storage' if args.mount_data else 'diagnostic'

r = Path(__file__).resolve().parents[1]
root = r / 'recovery/root'
for directory in ('system/etc', 'vendor/etc/vintf'):
    (root / directory).mkdir(parents=True, exist_ok=True)
(r / 'crypto-profile.json').write_text(json.dumps({
    'mode': mode, 'data_mount': args.mount_data, 'hardware_crypto_services': False
}, indent=2) + '\n')
(r / 'crypto-profile.mk').write_text(f'''# Storage mode uses plain userdata; diagnostic still compiles crypto.
TW_USE_FSCRYPT_POLICY := 2
TW_INCLUDE_CRYPTO := {str(not args.mount_data).lower()}
TW_INCLUDE_CRYPTO_FBE := {str(not args.mount_data).lower()}
TW_INCLUDE_FBE_METADATA_DECRYPT := false
BOARD_USES_METADATA_PARTITION := false
''')
fstab = '# Static dipper mounts; no guessed encryption/metadata options.\n'
for part in ('system', 'vendor'):
    for fs in ('ext4', 'erofs'):
        fstab += f'/dev/block/bootdevice/by-name/{part} /{part} {fs} ro wait,recoveryonly\n'
fstab += '\n'.join(extra_mounts()) + '\n'
data_lines = []
if args.mount_data:
    for fs in ('f2fs', 'ext4'):
        data_lines.append(f'/dev/block/bootdevice/by-name/userdata /data {fs} noatime,nosuid,nodev wait')
    fstab += '\n'.join(data_lines) + '\n'
fstab += '/dev/block/bootdevice/by-name/misc /misc emmc defaults defaults\n'
(r / 'recovery/recovery.fstab').write_text(fstab)
for relative in ('fstab.qcom', 'vendor/etc/fstab.qcom', 'system/etc/dipper-crypto.prop'):
    (root / relative).write_text('# Diagnostic mode: no installed-ROM crypto profile.\n')
if args.mount_data:
    for relative in ('fstab.qcom', 'vendor/etc/fstab.qcom'):
        (root / relative).write_text('\n'.join(data_lines) + '\n')
(root / 'vendor/etc/vintf/manifest.xml').write_text('<manifest version="1.0" type="device" />\n')
(root / 'init.recovery.dipper-crypto.rc').write_text('''# No hardware key service is started in the diagnostic build.
on init
    setprop dipper.crypto.ready 0
''')
(root / 'system/etc/twrp.flags').write_text(recovery_flags(data=args.mount_data))
print(f'{mode} profile generated: data_mount={args.mount_data}, no hardware decryption')
