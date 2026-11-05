#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Apply small checked fixes to the pinned core; never run a device operation."""
import sys
from pathlib import Path

core = Path(sys.argv[1])
updates = {}


def replace(relative, old, new):
    path = core / relative
    source = updates.get(path, path.read_text())
    if new in source:
        return
    if source.count(old) != 1:
        raise SystemExit(f'Unexpected pinned source in {relative}; runtime patch not applied')
    updates[path] = source.replace(old, new)


replace('partition.cpp', '#include <sys/stat.h>',
        '#include <sys/stat.h>\n#include <sys/wait.h>')
replace('partition.cpp', '''    if (TWFunc::ExecCmd(command) == 0) {
      gui2_console::info("done");
      return true;
    }
    gui2_console::log_error("unable_repair", display_name_);''', '''    // Preserve the exit code: e2fsck 1 means errors were corrected, while
    // 2 requires a reboot and 4+ must still stop a subsequent resize.
    const pid_t pid = fork();
    if (pid < 0) {
      gui2_console::log_error("unable_repair", display_name_);
      return false;
    }
    if (pid == 0) {
      execl("/system/bin/sh", "sh", "-c", command.c_str(), nullptr);
      _exit(127);
    }
    int status = -1;
    TWFunc::WaitForChild(pid, &status, command, false);
    const int code = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
    if (code == 0 || (std::string_view(binary) == "e2fsck" && code == 1)) {
      LOGINFO("Filesystem repair completed with exit code %d\\n", code);
      gui2_console::info("done");
      return true;
    }
    LOGERR("Filesystem repair failed or requires a reboot: exit code %d\\n", code);
    gui2_console::log_error("unable_repair", display_name_);''')

replace('gui2/backend/twrp_reboot_backend.cpp', '''bool twrp_reboot_backend::os_installed() const {
  const auto value = [](const char* name) {
    return std::strtoull(DataManager::GetStrValue(name).c_str(), nullptr, 10);
  };
  return value(TW_BACKUP_SYSTEM_SIZE) >= value(TW_MIN_SYSTEM_VAR);
}''', '''bool twrp_reboot_backend::os_installed() const {
  // Backup-size accounting may be deferred or unavailable for read-only
  // system images. Detect an actual Android installation instead.
  const std::string root = TWPartitionManager::GetAndroidRootPath();
  if (PartitionManager.FindPartitionByPath(root) == nullptr) return false;
  const bool was_mounted = PartitionManager.IsMountedByPath(root);
  if (!PartitionManager.MountByPath(root, false)) return false;
  bool installed = false;
  for (const auto& base : {root, root + "/system"}) {
    if (TWFunc::IsPathExists(base + "/build.prop") &&
        (TWFunc::IsPathExists(base + "/bin/init") ||
         TWFunc::IsPathExists(base + "/framework/framework.jar"))) {
      installed = true;
      break;
    }
  }
  if (!was_mounted) PartitionManager.UnmountByPath(root, false);
  return installed;
}''')

for path, content in updates.items():
    path.write_text(content)
print('Pinned core: checked fsck exit codes and Android system-file detection')
