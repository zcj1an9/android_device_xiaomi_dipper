#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare an all-or-nothing device matrix; never sync or compile anything."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def make_plan(catalog, requested, mode):
    devices = [name.strip() for name in requested.split(',')]
    targets = catalog.get('targets', {})
    if catalog.get('schema_version') != 1:
        raise ValueError('Unsupported target catalog version')
    if not devices or any(not re.fullmatch(r'[a-z0-9_]+', name) for name in devices):
        raise ValueError('Use a comma-separated list of device codenames')
    if len(set(devices)) != len(devices):
        raise ValueError('Duplicate devices are not allowed')
    if set(devices) - targets.keys():
        raise ValueError('Unknown device: ' + ', '.join(sorted(set(devices) - targets.keys())))
    if mode not in ('storage', 'diagnostic'):
        raise ValueError('Batch mode accepts storage or diagnostic; decrypt needs individual profiles')
    entries, blocked = [], []
    for device in devices:
        target = targets[device]
        reasons = []
        if target.get('build_enabled') is not True:
            reasons.append('builds disabled')
        if target.get('validation') != 'passed':
            reasons.append('device validation pending')
        if mode not in target.get('modes', []):
            reasons.append('mode not validated')
        repository = target.get('repository') or ''
        ref = target.get('ref') or ''
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            reasons.append('device repository missing')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', ref) or '..' in ref:
            reasons.append('device source ref missing/invalid')
        if target.get('device_path') != f'device/xiaomi/{device}' or target.get('product') != device:
            reasons.append('device path/product mismatch')
        lunch = target.get('lunch') or ''
        if not re.fullmatch(r'twrp_' + re.escape(device) + r'-[A-Za-z0-9_]+-userdebug', lunch):
            reasons.append('device lunch target missing/invalid')
        source_lock = target.get('source_lock') or ''
        if not re.fullmatch(re.escape(device) + r'-source-lock\.xml', source_lock):
            reasons.append('device provenance filename missing/invalid')
        if reasons:
            blocked.append({'device': device, 'reasons': reasons, 'pending': target.get('pending', [])})
        entries.append({key: target.get(key) for key in
                        ('repository', 'ref', 'device_path', 'product', 'lunch', 'source_lock')}
                       | {'device': device, 'mode': mode})
    ready = not blocked
    # Do not quietly build only dipper when a three-device batch was requested.
    return {'ready': ready, 'requested': devices, 'mode': mode, 'blocked': blocked,
            'matrix': {'include': entries if ready else []}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--devices', default='dipper,perseus,equuleus')
    parser.add_argument('--mode', default='storage')
    parser.add_argument('--catalog', type=Path, default=ROOT / 'devices/targets.json')
    parser.add_argument('--output', type=Path, help='GitHub output file, if requested')
    parser.add_argument('--summary', type=Path, help='GitHub summary file, if requested')
    parser.add_argument('--require-ready', action='store_true')
    args = parser.parse_args()
    try:
        plan = make_plan(json.loads(args.catalog.read_text()), args.devices, args.mode)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(plan, indent=2))
    if args.output:
        with args.output.open('a') as stream:
            stream.write('ready=' + str(plan['ready']).lower() + '\n')
            stream.write('matrix=' + json.dumps(plan['matrix'], separators=(',', ':')) + '\n')
    if args.summary:
        with args.summary.open('a') as stream:
            stream.write('Requested devices: ' + ', '.join(plan['requested']) + '\n\n')
            stream.write('Build ready: ' + str(plan['ready']) + '\n\n')
            for row in plan['blocked']:
                stream.write('- ' + row['device'] + ': ' + '; '.join(row['reasons']) + '\n')
    if args.require_ready and not plan['ready']:
        raise SystemExit('Batch blocked before source download: requested devices are not all ready')


if __name__ == '__main__':
    main()
