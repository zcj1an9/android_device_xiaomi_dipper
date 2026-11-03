#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stream resource evidence into the job log, even if artifact upload cannot run."""
import datetime
import pathlib
import shutil
import subprocess
import sys
import time

source = pathlib.Path(sys.argv[1])
log = pathlib.Path(sys.argv[2])
while True:
    values = {}
    for line in pathlib.Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        values[key] = int(value.split()[0])
    memory = f'mem_available_MiB={values["MemAvailable"] // 1024} swap_free_MiB={values["SwapFree"] // 1024}'
    disk = f'disk_free_GiB={shutil.disk_usage(source).free // (1024 ** 3)}'
    processes = subprocess.run(['ps', '-eo', 'pid,comm,rss', '--sort=-rss'],
                               capture_output=True, text=True, check=False)
    top = ' | '.join(processes.stdout.splitlines()[1:5]).strip()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    line = f'{timestamp} resources: {memory} {disk}; top_RSS_KiB: {top}\n'
    with log.open('a') as stream:
        stream.write(line)
    print(line, end='', flush=True)
    for path in ('/proc/pressure/memory', '/sys/fs/cgroup/memory.events'):
        try:
            content = pathlib.Path(path).read_text().strip().replace('\n', '; ')
        except OSError:
            continue
        record = f'{timestamp} {path}: {content}\n'
        with log.open('a') as stream:
            stream.write(record)
        print(record, end='', flush=True)
    time.sleep(60)
