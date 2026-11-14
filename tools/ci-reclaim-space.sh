#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Only for a disposable Actions checkout, after repo manifest -r is saved.
set -euo pipefail
source_dir=${1:?Usage: ci-reclaim-space.sh /path/to/android-source}
[[ ${GITHUB_ACTIONS:-} == true ]] || { echo 'Refusing cleanup outside GitHub Actions'; exit 1; }
source_dir=$(realpath -- "$source_dir")
[[ -n ${GITHUB_WORKSPACE:-} && "$source_dir" == "$(realpath -- "$GITHUB_WORKSPACE")/android-source" ]] || {
    echo 'Refusing cleanup outside the disposable android-source directory'; exit 1;
}
test -s "$source_dir/perseus-source-lock.xml"
test -f "$source_dir/build/envsetup.sh"
test -d "$source_dir/.repo"
echo 'Disk usage before removing synced Git object stores:'
df -h "$source_dir"
du -sh "$source_dir/.repo/project-objects" "$source_dir/.repo/projects" 2>/dev/null || true
# The pinned working files and source-lock manifest remain. This job never
# syncs again; removing these stores means its Android checkout is disposable.
# Keep manifests/repo metadata used by build tooling; do not remove source files.
rm -rf -- "$source_dir/.repo/project-objects" "$source_dir/.repo/projects"
echo 'Disk usage after removing synced Git object stores:'
df -h "$source_dir"
available=$(df --output=avail -B1 "$source_dir" | tail -1)
if (( available < 30 * 1024 * 1024 * 1024 )); then
    echo '::error::Less than 30 GiB free after source sync and CI cleanup; refusing a build that may exhaust the runner disk.'
    du -h -d 2 "$source_dir" 2>/dev/null | sort -h | tail -25
    exit 1
fi

