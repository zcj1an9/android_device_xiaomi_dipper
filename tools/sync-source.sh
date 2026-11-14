#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_dir=${1:?Usage: sync-source.sh /path/to/new/android-source}
command -v repo >/dev/null || { echo 'Install the Android repo launcher first'; exit 1; }
mkdir -p "$source_dir"
cd "$source_dir"
repo init --depth=1 -u https://github.com/TWRP-Test/platform_manifest_twrp_aosp.git -b 814b553116ceedde197f70389cff9661d81d8337
mkdir -p .repo/local_manifests
cp "$package_dir/manifests/perseus-core.xml" .repo/local_manifests/
repo sync -c --no-tags --no-clone-bundle -j"${RECOVERY_SYNC_JOBS:-4}"
repo manifest -r -o perseus-source-lock.xml
python3 "$package_dir/tools/preflight.py"

