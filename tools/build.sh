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
unset ALLOW_MISSING_DEPENDENCIES
source build/envsetup.sh
# Android 16's release-config lunch syntax. Override only if your source differs.
lunch "${DIPPER_LUNCH:-twrp_dipper-bp2a-userdebug}"
m -j"${DIPPER_JOBS:-4}" recoveryimage 2>&1 | tee dipper-recovery-build.log
test -s out/target/product/dipper/recovery.img
test "$(stat -c%s out/target/product/dipper/recovery.img)" -le 67108864
sha256sum out/target/product/dipper/recovery.img
