#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compile crypto code without mounting data or starting hardware crypto HALs."""
import json
from pathlib import Path

r = Path(__file__).resolve().parents[1]
root = r / 'recovery/root'
for directory in ('system/etc', 'vendor/etc/vintf'):
    (root / directory).mkdir(parents=True, exist_ok=True)
(r / 'crypto-profile.json').write_text(json.dumps({
    'mode': 'diagnostic', 'data_mount': False, 'hardware_crypto_services': False
}, indent=2) + '\n')
(r / 'crypto-profile.mk').write_text('''# Diagnostic image: compile crypto, do not decrypt existing data.
TW_USE_FSCRYPT_POLICY := 2
TW_INCLUDE_CRYPTO := true
TW_INCLUDE_CRYPTO_FBE := true
TW_INCLUDE_FBE_METADATA_DECRYPT := false
BOARD_USES_METADATA_PARTITION := false
''')
fstab = '# Diagnostic: /data and /metadata intentionally omitted.\n'
for part in ('system', 'vendor'):
    for fs in ('ext4', 'erofs'):
        fstab += f'/dev/block/bootdevice/by-name/{part} /{part} {fs} ro wait,recoveryonly\n'
fstab += '/dev/block/bootdevice/by-name/misc /misc emmc defaults defaults\n'
(r / 'recovery/recovery.fstab').write_text(fstab)
for relative in ('fstab.qcom', 'vendor/etc/fstab.qcom', 'system/etc/dipper-crypto.prop'):
    (root / relative).write_text('# Diagnostic mode: no installed-ROM crypto profile.\n')
(root / 'vendor/etc/vintf/manifest.xml').write_text('<manifest version="1.0" type="device" />\n')
(root / 'init.recovery.dipper-crypto.rc').write_text('''# No hardware key service is started in the diagnostic build.
on init
    setprop dipper.crypto.ready 0
''')
(root / 'system/etc/twrp.flags').write_text('''/boot emmc /dev/block/bootdevice/by-name/boot flags=display="Boot";backup=1
/recovery emmc /dev/block/bootdevice/by-name/recovery flags=display="Recovery";backup=1;flashimg=1
/usb_otg auto /dev/block/sdg1 /dev/block/sdg flags=display="USB-OTG";storage;removable
''')
print('Diagnostic profile generated: no data mount and no hardware decryption')
