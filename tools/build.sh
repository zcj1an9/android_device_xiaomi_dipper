#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Run inside an already synced TWRP-Test twrp-16.0 source checkout.
set -eo pipefail
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_dir=${1:-$PWD}
cd "$source_dir"
test -f build/envsetup.sh || { echo 'Not an Android source checkout'; exit 1; }
test -f "$package_dir/crypto-profile.mk" || { echo 'Run configure.py first'; exit 1; }
bash "$package_dir/tools/fetch-prebuilts.sh"
test -d system/vold || exit 1
# Fail before compilation when an older decrypt core was synced accidentally.
grep -q 'Gatekeeper_Verify' system/vold/Decrypt.cpp || { echo 'Wrong/older vold fork'; exit 1; }
grep -q 'syncKeystoreDb' system/vold/Decrypt.cpp || { echo 'Missing modern synthetic-password path'; exit 1; }
if [[ -e device/xiaomi/dipper && "$(cd device/xiaomi/dipper && pwd)" != "$package_dir" ]]; then
    echo 'device/xiaomi/dipper exists. Move it aside explicitly before installing this tree.'
    exit 1
fi
mkdir -p device/xiaomi
if [[ ! -e device/xiaomi/dipper ]]; then
    cp -a "$package_dir" device/xiaomi/dipper
fi
# Keep a single installer for /init.recovery.usb.rc: the core Soong prebuilt.
# Feed it the device's configfs rules instead of also copying that destination
# from PRODUCT_COPY_FILES. This runs before envsetup/Soong on local and CI builds.
test -f bootable/recovery/etc/init.recovery.usb.rc || { echo 'Missing core USB init prebuilt'; exit 1; }
cp device/xiaomi/dipper/recovery/root/init.recovery.usb.rc bootable/recovery/etc/init.recovery.usb.rc
# Recovery must remain accessible if experimental keystore2 cannot load a blob.
# This changes only the recovery service restart policy, not the installed ROM.
python3 - <<'PY'
from pathlib import Path
p = Path('bootable/recovery/etc/init/keystore2.rc')
s = p.read_text()
lines = s.splitlines(True)
p.write_text(''.join(x for x in lines if not x.lstrip().startswith('critical ')
                   and 'Reboot to bootloader if Keystore' not in x))
PY
# Required by this upstream minimal manifest: it omits projects referenced by
# unrelated CTS/emulator/test modules which Soong still discovers globally.
# Keep recoveryimage's exit status and image existence/size checks below.
export ALLOW_MISSING_DEPENDENCIES=true
printf 'Upstream minimal-manifest mode: ALLOW_MISSING_DEPENDENCIES=%s\n' "$ALLOW_MISSING_DEPENDENCIES"
source build/envsetup.sh
# Android 16's release-config lunch syntax. Override only if your source differs.
lunch "${DIPPER_LUNCH:-twrp_dipper-bp2a-userdebug}"
m -j"${DIPPER_JOBS:-4}" recoveryimage 2>&1 | tee dipper-recovery-build.log
test -s out/target/product/dipper/recovery.img
test "$(stat -c%s out/target/product/dipper/recovery.img)" -le 67108864
sha256sum out/target/product/dipper/recovery.img
