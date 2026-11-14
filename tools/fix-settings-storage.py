#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Adjust the pinned TWRP core to keep settings on the device's writable cache."""
import sys
from pathlib import Path

core = Path(sys.argv[1])
updates = {}


def replace(relative, old, new, count=1):
    path = core / relative
    source = updates.get(path, path.read_text())
    if new in source:
        return
    if source.count(old) != count:
        raise SystemExit(f'Unexpected recovery source in {relative}; settings patch not applied')
    updates[path] = source.replace(old, new)


replace('variables.h', '#define TW_PERSIST_ROOT             "/mnt/vendor/persist"',
        '#define TW_PERSIST_ROOT             "/cache"')
replace('infomanager.cpp', '#include <sys/stat.h>',
        '#include <sys/stat.h>\n#include <unistd.h>\n#include <cerrno>')
replace('infomanager.cpp', '''static bool twPersistFirstMounted = false;

static void twPersistMount() {
  twPersistFirstMounted = PartitionManager.IsMountedByPath(TW_PERSIST_DIR);
  if (!twPersistFirstMounted) PartitionManager.MountByPath(TW_PERSIST_DIR, false);
}''', '''static bool twPersistMount() {
  if (!PartitionManager.MountByPath(TW_PERSIST_ROOT, false)) {
    LOGERR("Cannot mount '%s' for TWRP settings\\n", TW_PERSIST_ROOT);
    return false;
  }
  if (mkdir(TW_PERSIST_DIR, 0770) != 0 && errno != EEXIST) {
    LOGERR("Cannot create TWRP settings directory '%s'\\n", TW_PERSIST_DIR);
    return false;
  }
  return true;
}''')
replace('infomanager.cpp', '  twPersistMount();',
        '  if (!twPersistMount()) return -1;', count=2)
replace('infomanager.cpp', '  fwrite(out.data(), 1, out.size(), file.get());',
        '''  if (fwrite(out.data(), 1, out.size(), file.get()) != out.size() ||
      fflush(file.get()) != 0 || fsync(fileno(file.get())) != 0) {
    LOGERR("Failed to write TWRP settings to '%s'\\n", file_.c_str());
    return -1;
  }''')
replace('data.cpp', '''  persist_.SaveValues();
  pthread_mutex_unlock(&values_lock_);

  tw_set_default_metadata(kBackingFile.c_str());''', '''  const int save_status = persist_.SaveValues();
  pthread_mutex_unlock(&values_lock_);
  if (save_status != 0) {
    LOGERR("Failed to save settings file '%s'\\n", kBackingFile.c_str());
    return save_status;
  }

  tw_set_default_metadata(kBackingFile.c_str());''')

for path, content in updates.items():
    path.write_text(content)
print('TWRP settings: /cache/TWRP/.twrp_settings; mount/write errors are checked')

