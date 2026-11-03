#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Fetch only the upstream kernel and proprietary files listed in PREBUILTS.sha256.
set -euo pipefail
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if (cd "$package_dir" && sha256sum -c PREBUILTS.sha256 >/dev/null 2>&1); then
    echo 'Pinned prebuilts already present and verified'
    exit 0
fi
temp_dir=$(mktemp -d)
trap 'rm -rf -- "$temp_dir"' EXIT
fetch_tree() {
    local url=$1 sha=$2 target=$3
    git init -q "$target"
    git -C "$target" remote add origin "$url"
    git -C "$target" fetch --depth=1 origin "$sha"
    git -C "$target" checkout -q --detach FETCH_HEAD
    test "$(git -C "$target" rev-parse HEAD)" = "$sha"
}
fetch_tree https://gitlab.com/OrangeFox/device/dipper.git 42f273eba9a39281c523cec361aa68a8ac5ef298 "$temp_dir/dipper"
fetch_tree https://gitlab.com/OrangeFox/device/sdm845-common.git 4145d071ae1e86a245354215638946e85711204a "$temp_dir/common"
mkdir -p "$package_dir/prebuilt"
cp "$temp_dir/dipper/prebuilt/419/Image.gz-dtb" "$package_dir/prebuilt/"
while read -r hash relative; do
    case "$relative" in
        prebuilt/Image.gz-dtb) continue ;;
        recovery/root/*)
            source_path=${relative#recovery/root/}
            mkdir -p "$(dirname "$package_dir/$relative")"
            cp "$temp_dir/common/recovery/root/$source_path" "$package_dir/$relative"
            ;;
        *) echo "Unexpected prebuilt path: $relative" >&2; exit 1 ;;
    esac
done < "$package_dir/PREBUILTS.sha256"
(cd "$package_dir" && sha256sum -c PREBUILTS.sha256)
