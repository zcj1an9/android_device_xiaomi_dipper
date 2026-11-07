#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Disposable CI source build: no install, flashing, or writes to the phone.
set -euo pipefail
device=${1:?Usage: build-recovery-kernel.sh DEVICE OUTPUT_DIRECTORY}
output_dir=$(realpath -m -- "${2:?Output directory required}")
case "$device" in equuleus|perseus) ;; *) exit 2 ;; esac
mkdir -p "$output_dir"
source_dir="$output_dir/source"
fetch() {
    local url=$1 revision=$2 destination=$3
    test ! -e "$destination" || { echo "Refusing to overwrite $destination"; exit 1; }
    git init -q "$destination"
    git -C "$destination" remote add origin "$url"
    git -C "$destination" fetch --depth=1 origin "$revision"
    git -C "$destination" checkout -q --detach FETCH_HEAD
    test "$(git -C "$destination" rev-parse HEAD)" = "$revision"
}
# Keep the stable common test baseline; recovery does not need the AOD candidate.
fetch https://github.com/zcj1an9/android_kernel_xiaomi_sdm845_419.git 49f75ba72af749092196b29348b98dbd1d8a19eb "$source_dir"
# Existing external dependencies of this kernel; used only in this disposable
# build checkout, never added to the kernel GitHub repository.
fetch https://github.com/duckyduckG/kernel_techpack_mi845_419.git 87be21823dfeeca50735ae575f2c1b51f348cb70 "$source_dir/techpack/mi845"
fetch https://github.com/duckyduckG/devicetree_qcom-sdm845_419.git be1279422f14437df8c185f952b4139ff7e10157 "$source_dir/arch/arm64/boot/dts/qcom-sdm845"
fetch https://github.com/duckyduckG/devicetree_xiaomi_419.git c573577e1fb2e92f36f9546d2e45738e618316af "$source_dir/arch/arm64/boot/dts/xiaomi"
export CLANG_BIN=/usr/lib/llvm-14/bin
export JOBS=${DIPPER_JOBS:-2}
export OUT_DIR="$output_dir/out"
export CROSS_COMPILE=aarch64-linux-gnu-
export CROSS_COMPILE_ARM32=arm-linux-gnueabi-
"$CLANG_BIN/clang" --version
bash "$source_dir/scripts/build-perf-a17.sh" "$device" 2>&1 | tee "$output_dir/kernel-build.log"
release=$(cat "$OUT_DIR/include/config/kernel.release")
[[ "$release" == 4.19.* ]] || { echo "Unexpected kernel release: $release"; exit 1; }
if [[ "$device" == equuleus ]]; then
    grep -qx 'CONFIG_MACH_XIAOMI_E1S=y' "$OUT_DIR/.config"
    ! grep -qx 'CONFIG_MACH_XIAOMI_E5=y' "$OUT_DIR/.config"
else
    grep -qx 'CONFIG_MACH_XIAOMI_E5=y' "$OUT_DIR/.config"
    ! grep -qx 'CONFIG_MACH_XIAOMI_E1S=y' "$OUT_DIR/.config"
fi
cp "$OUT_DIR/arch/arm64/boot/Image.gz-dtb" "$output_dir/Image.gz-dtb"
cp "$OUT_DIR/.config" "$output_dir/kernel.config"
printf '%s\n' "$release" > "$output_dir/kernel-release.txt"
# Preserve built device overlays for pairing review. Do not construct or flash
# a DTBO table using guessed hardware IDs/revisions.
mkdir -p "$output_dir/overlays"
while IFS= read -r -d '' file; do cp "$file" "$output_dir/overlays/"; done < <(find "$OUT_DIR/arch/arm64/boot/dts/xiaomi" -name '*.dtbo' -print0)
if [[ "$device" == perseus ]]; then
    test -s "$output_dir/overlays/perseus-mp-v2.1-overlay.dtbo"
fi
python3 - "$device" "$output_dir" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[2])
x={'device':sys.argv[1], 'kernel_release':(p/'kernel-release.txt').read_text().strip(),
   'repository':'zcj1an9/android_kernel_xiaomi_sdm845_419',
   'commit':'49f75ba72af749092196b29348b98dbd1d8a19eb',
   'sha256':hashlib.sha256((p/'Image.gz-dtb').read_bytes()).hexdigest(),
   'dtbo_flashed':False,
   'overlays':[x.name for x in (p/'overlays').glob('*.dtbo')]}
(p/'kernel-provenance.json').write_text(json.dumps(x,indent=2)+'\n')
PY
# Source and provenance remain reproducible from fixed commits. Reclaim object
# stores before syncing Android to avoid exhausting this disposable CI runner.
tar -czf "$output_dir/kernel-device-trees.tar.gz" -C "$source_dir/arch/arm64/boot/dts" xiaomi
rm -rf -- "$output_dir/source" "$output_dir/out"
