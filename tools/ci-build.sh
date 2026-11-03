#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -eo pipefail
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_dir=${1:?Usage: ci-build.sh /path/to/android-source}
log_dir=${GITHUB_WORKSPACE:-$PWD}
python3 "$package_dir/tools/ci-resource-monitor.py" "$source_dir" "$log_dir/resource-usage.log" &
monitor_pid=$!
cleanup() {
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
    {
        free -h
        df -h "$source_dir"
        sudo -n dmesg 2>&1 | tail -n 100
    } > "$log_dir/runner-diagnostics.txt" 2>&1 || true
}
trap cleanup EXIT
nofile_limit=$(ulimit -Hn)
if [[ "$nofile_limit" == unlimited || "$nofile_limit" -gt 65535 ]]; then
    nofile_limit=65535
fi
ulimit -n "$nofile_limit"
bash "$package_dir/tools/build.sh" "$source_dir" 2>&1 | tee "$log_dir/build-console.log"
