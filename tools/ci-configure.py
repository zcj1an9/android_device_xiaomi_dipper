#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Translate workflow input to a checked argument list, never shell source."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
mode = os.environ.get('BUILD_MODE', 'diagnostic')
if mode == 'diagnostic':
    subprocess.run([sys.executable, str(root / 'tools/configure-diagnostic.py')], check=True)
elif mode == 'decrypt':
    profile = json.loads(os.environ.get('CRYPTO_PROFILE', '') or '{}')
    allowed = {
        'keymaster', 'policy', 'fileencryption', 'os_version', 'security_patch',
        'vendor_patch', 'metadata_partition', 'metadata_encryption', 'keydirectory',
        'dm_options_version', 'wrapped_key'
    }
    if not isinstance(profile, dict) or set(profile) - allowed:
        raise SystemExit('Invalid crypto profile keys; see ACTIONS.md')
    args = [sys.executable, str(root / 'tools/configure.py')]
    for key, value in profile.items():
        if key == 'wrapped_key':
            if type(value) is not bool:
                raise SystemExit('wrapped_key must be boolean')
            if value:
                args.append('--wrapped-key')
        elif type(value) not in (str, int):
            raise SystemExit(f'Invalid value type for {key}')
        else:
            args.extend(['--' + key.replace('_', '-'), str(value)])
    subprocess.run(args, check=True)
else:
    raise SystemExit('Unsupported build mode')
