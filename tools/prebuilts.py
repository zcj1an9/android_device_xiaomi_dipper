# SPDX-License-Identifier: Apache-2.0
"""Validate the binary payloads before import or a long recovery build."""
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def fdt(data):
    if len(data) < 40 or data[:4] != bytes.fromhex('d00dfeed'):
        raise ValueError('Missing FDT header')
    total = struct.unpack_from('>I', data, 4)[0]
    if not 40 <= total <= len(data):
        raise ValueError('Invalid FDT size')
    return total

def kernel(data):
    stream = zlib.decompressobj(16 + zlib.MAX_WBITS)
    image = stream.decompress(data)
    if not stream.eof or not re.search(rb'Linux version 4\.19\.', image):
        raise ValueError('Expected a gzip-compressed Linux 4.19 kernel')
    tail = stream.unused_data
    count = 0
    while tail:
        total = fdt(tail)
        tail = tail[total:]
        count += 1
    if not count:
        raise ValueError('Kernel must contain appended base DTB(s)')

def dtbo(data):
    if len(data) < 32:
        raise ValueError('Truncated DTBO header')
    magic,total,header,entry_size,count,offset,page,version = struct.unpack_from('>8I',data)
    if (magic != 0xd7b7ab1e or not 32 <= total <= len(data)
            or header != 32 or entry_size != 32 or not 0 < count < 256
            or offset < header or offset+count*entry_size > total
            or page != 4096 or version != 0):
        raise ValueError('Invalid DTBO table')
    end = offset+count*entry_size
    for i in range(count):
        size,start = struct.unpack_from('>2I',data,offset+i*entry_size)
        if start < end or size < 40 or start+size > total:
            raise ValueError('DTBO entry exceeds table bounds')
        if fdt(data[start:start+size]) != size:
            raise ValueError('DTBO entry size mismatch')
    if any(data[total:]):
        raise ValueError('Unexpected nonzero bytes after DTBO table')

def validate_pair(kernel_data, dtbo_data, pins):
    kernel(kernel_data)
    dtbo(dtbo_data)
    for name,data in [('Image.gz-dtb',kernel_data),('dtbo.img',dtbo_data)]:
        expected = pins['files'].get(name)
        if expected and digest(data) != expected:
            raise ValueError(f'{name} differs from the pinned bootable reference')

def verify(root=ROOT):
    pins = json.loads((root/'prebuilt/manifest.json').read_text())
    if not all(pins['files'].get(name) for name in ('Image.gz-dtb','dtbo.img')):
        raise ValueError('Prebuilts pending: import this device\'s kernel and DTBO first')
    k=(root/'prebuilt/Image.gz-dtb').read_bytes()
    d=(root/'prebuilt/dtbo.img').read_bytes()
    validate_pair(k,d,pins)
    expected=''.join(f'{digest(data)}  prebuilt/{name}\n' for name,data in [('Image.gz-dtb',k),('dtbo.img',d)])
    if (root/'PREBUILTS.sha256').read_text()!=expected:
        raise ValueError('PREBUILTS.sha256 does not match both files')
    return pins
