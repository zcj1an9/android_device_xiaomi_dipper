# SPDX-License-Identifier: Apache-2.0
"""Shared static dipper partitions for diagnostic, storage and decrypt builds."""

BLOCK = '/dev/block/bootdevice/by-name/'


def extra_mounts(metadata_partition='none'):
    # Mount locations/types match the supplied ROM fstab. Cust is its own mount,
    # not an alias for system_ext. Never expose one block as both cust/metadata.
    entries = [
        ('cache', '/cache', 'ext4', 'noatime,nosuid,nodev'),
        ('cache', '/cache', 'f2fs', 'noatime,nosuid,nodev'),
        ('persist', '/persist', 'ext4', 'ro,noload,nosuid,nodev'),
        ('modem', '/firmware', 'vfat', 'ro,shortname=lower'),
        ('dsp', '/dsp', 'ext4', 'ro,noload,nosuid,nodev'),
        ('bluetooth', '/bt_firmware', 'vfat', 'ro,shortname=lower'),
    ]
    if metadata_partition != 'cust':
        entries += [('cust', '/cust', 'ext4', 'ro,noload,nosuid,nodev'),
                    ('cust', '/cust', 'erofs', 'ro')]
    return [f'{BLOCK}{part} {mount} {fs} {opts} wait,recoveryonly'
            for part, mount, fs, opts in entries]


def recovery_flags(metadata_partition='none', decrypt=False, data=False):
    lines = ['# mount point type block device flags']
    for part, title in [('boot', 'Boot'), ('recovery', 'Recovery'), ('dtbo', 'DTBO')]:
        lines.append(f'/{part} emmc {BLOCK}{part} flags=display="{title}";backup=1;flashimg=1;canbewiped=0;wipeingui=0')
    for part, title in [('system', 'System'), ('vendor', 'Vendor')]:
        lines.append(f'/{part} ext4 {BLOCK}{part} flags=display="{title}";backup=1')
    # Raw image names follow TeamWin's dipper recovery tree. Separate mount
    # points permit choosing file backup or a full partition image explicitly.
    images = [
        ('system_image', 'system', 'System Image', True, None),
        ('vendor_image', 'vendor', 'Vendor Image', True, None),
        ('persist_image', 'persist', 'Persist Image', False, None),
        ('modem', 'modem', 'Modem Firmware Image', False, None),
        ('bluetooth_image', 'bluetooth', 'Bluetooth Firmware Image', False, '/modem'),
        ('dsp_image', 'dsp', 'DSP Image', False, '/modem'),
        ('efs1', 'modemst1', 'EFS', False, None),
        ('efs2', 'modemst2', 'EFS modemst2', False, '/efs1'),
        ('efsc', 'fsc', 'EFS fsc', False, '/efs1'),
        ('efsg', 'fsg', 'EFS fsg', False, '/efs1'),
    ]
    if metadata_partition != 'cust':
        images.append(('cust_image', 'cust', 'Cust Image', True, None))
    for mount, part, title, flash, parent in images:
        flags = f'display="{title}";backup=1;flashimg={int(flash)};canbewiped=0;wipeingui=0'
        if parent:
            flags += f';subpartitionof={parent}'
        lines.append(f'/{mount} emmc {BLOCK}{part} flags={flags}')
    for mount, fs, part, title in [
        ('cache', 'ext4', 'cache', 'Cache'),
        ('cust', 'ext4', 'cust', 'Cust'),
        ('persist', 'ext4', 'persist', 'Persist'),
        ('firmware', 'vfat', 'modem', 'Firmware'),
        ('dsp', 'ext4', 'dsp', 'DSP'),
        ('bt_firmware', 'vfat', 'bluetooth', 'Bluetooth Firmware'),
    ]:
        if part == 'cust' and metadata_partition == 'cust':
            continue
        flags = f'display="{title}";backup=1'
        if part != 'cache':
            flags += ';canbewiped=0;wipeingui=0'
        if decrypt and part in ('persist', 'modem'):
            flags += ';mounttodecrypt'
        lines.append(f'/{mount} {fs} {BLOCK}{part} flags={flags}')
    if data:
        lines.append(f'/data f2fs {BLOCK}userdata flags=display="Data";backup=1')
    if metadata_partition != 'none':
        lines.append(f'/metadata ext4 {BLOCK}{metadata_partition} flags=display="Metadata";backup=1;mounttodecrypt;canbewiped=0;wipeingui=0')
    lines.append('/usb_otg auto /dev/block/sdg1 /dev/block/sdg flags=display="USB-OTG";storage;removable')
    return '\n'.join(lines) + '\n'
