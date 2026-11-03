# Sources and licensing

This is an experimental standalone recovery device tree, not a kernel fork.

| Component | Upstream | Revision |
|---|---|---|
| dipper kernel prebuilt | https://gitlab.com/OrangeFox/device/dipper | `42f273eba9a39281c523cec361aa68a8ac5ef298`, `prebuilt/419/Image.gz-dtb` |
| QTI prebuilts, USB init | https://gitlab.com/OrangeFox/device/sdm845-common | `4145d071ae1e86a245354215638946e85711204a` |
| Original dipper hardware layout, ueventd | https://github.com/LucyfMorning/twrp_device_xiaomi_dipper | `3edb97ccd2dfc92cf8af10a4f6abbdc646c75676` |
| Android manifest | https://github.com/TWRP-Test/platform_manifest_twrp_aosp | `814b553116ceedde197f70389cff9661d81d8337` |
| Recovery core | https://github.com/TWRP-Test/android_bootable_recovery | `8a58fc3b586b8a908337fa87529cfbbb119ec7bb` |
| vold / synthetic-password decryption | https://github.com/TWRP-Test/android_system_vold | `e7e26ed2ffd9ad0469a05515cfd91940a3366d19` |

The upstream dipper README identifies the 4.19 kernel source as
https://github.com/duckyduckG/android_kernel_xiaomi_sdm845_419 on
`lineage-23.2_xiaomi`. The exact kernel source commit that produced the supplied
binary is not recorded in that README; this project does not claim a reproducible
kernel source-to-binary match. The binary is fetched from the pinned device-tree
revision and checked against PREBUILTS.sha256. No V1.71 binary is used.

New configuration/scripts are under Apache-2.0, identified by SPDX headers.
USB init and ueventd preserve their upstream license headers. Linux kernel
licensing is GPL-2.0; COPYING is included. OrangeFox scripts/configuration are
GPL-3.0-or-later where indicated upstream; LICENSE.GPL-3.0 is included for reference.
Qualcomm/other vendor ELF files remain proprietary upstream material: no ownership
or new license is asserted. They are fetched separately instead of republished
as newly authored source.

`tools/build.sh` applies two local adjustments to the pinned recovery checkout:
it supplies the device's USB init contents to the core Soong prebuilt (the sole
installer of `/init.recovery.usb.rc`), and removes the critical restart policy
from recovery's keystore2 service. Always build through this script, including
for manual builds, so these adjustments are applied before Soong runs.
