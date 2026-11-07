#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check generated recovery boot arguments before kernel/source builds."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'prepare_other_device', ROOT / 'tools/prepare-other-device.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

# Match platform/build android-16.0.0_r1 core/Makefile's ifdef behavior.
# false is nonempty, so it still enables --recovery_dtbo.
RULES = """
include BoardConfig.mk
INTERNAL_RECOVERYIMAGE_ARGS := $(BOARD_MKBOOTIMG_ARGS)
ifdef BOARD_INCLUDE_RECOVERY_DTBO
ifdef BOARD_PREBUILT_RECOVERY_DTBOIMAGE
INTERNAL_RECOVERYIMAGE_ARGS += --recovery_dtbo $(BOARD_PREBUILT_RECOVERY_DTBOIMAGE)
else
INTERNAL_RECOVERYIMAGE_ARGS += --recovery_dtbo $(BOARD_PREBUILT_DTBOIMAGE)
endif
endif
ifdef BOARD_INCLUDE_RECOVERY_ACPIO
INTERNAL_RECOVERYIMAGE_ARGS += --recovery_acpio $(BOARD_RECOVERY_ACPIO)
endif
ifdef BOARD_INCLUDE_DTB_IN_BOOTIMG
INTERNAL_RECOVERYIMAGE_ARGS += --dtb $(INSTALLED_DTBIMAGE_TARGET)
endif
.PHONY: check
check:
\t$(file >report.txt,header=$(BOARD_BOOTIMG_HEADER_VERSION))
\t$(file >>report.txt,legacy_header=$(BOARD_BOOT_HEADER_VERSION))
\t$(file >>report.txt,include_dtbo=$(strip $(BOARD_INCLUDE_RECOVERY_DTBO)))
\t$(file >>report.txt,args=$(strip $(INTERNAL_RECOVERYIMAGE_ARGS)))
\t@:
"""


def validate_board(board):
    with tempfile.TemporaryDirectory(prefix='twrp-layout-') as temp:
        root = Path(temp)
        # The bring-up crypto fragment does not alter boot-image layout.
        for device in ('equuleus', 'perseus'):
            crypto = root / 'device/xiaomi' / device / 'crypto-profile.mk'
            crypto.parent.mkdir(parents=True)
            crypto.write_text('# Bring-up crypto profile has no boot layout overrides.\n')
        (root / 'BoardConfig.mk').write_text(board)
        (root / 'check.mk').write_text(RULES)
        subprocess.run(['make', '--no-print-directory', '-s', '-f', 'check.mk', 'check'],
                       cwd=root, check=True, timeout=15)
        values = dict(line.split('=', 1) for line in
                      (root / 'report.txt').read_text().splitlines())
    if values['header'] != '0' or values['legacy_header'] != '0':
        raise ValueError('Bring-up recovery requires boot header 0')
    if values['include_dtbo']:
        raise ValueError('BOARD_INCLUDE_RECOVERY_DTBO must be empty, not false')
    args = shlex.split(values['args'])
    forbidden = {'--recovery_dtbo', '--recovery_acpio', '--dtb'}
    if forbidden.intersection(args):
        raise ValueError('Unexpected embedded DTB/DTBO/ACPIO argument: ' + values['args'])
    if args.count('--header_version') != 1:
        raise ValueError('Expected one boot header argument')
    pos = args.index('--header_version')
    if pos + 1 >= len(args) or args[pos + 1] != '0':
        raise ValueError('mkbootimg header argument does not match the board')
    return values['args']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--device', choices=['equuleus', 'perseus'], required=True)
    args = parser.parse_args()
    profiles = json.loads((ROOT / 'devices/bringup-targets.json').read_text())
    board = generator.prepare_board(
        args.device, profiles[args.device], (args.base / 'BoardConfig.mk').read_text())
    checked = validate_board(board)
    print(f'{args.device}: boot layout PASS; mkbootimg args: {checked}')


if __name__ == '__main__':
    main()
