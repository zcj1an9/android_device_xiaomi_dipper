# dipper prebuilts

Upload this device's files directly here:

- `Image.gz-dtb`: device-specific kernel with appended base DTB(s)
- `dtbo.img`: this device's DTBO

Actions and local build scripts use these files directly. No import script, hash match, format validator or checksum-manifest registration is required. Files are neither downloaded nor replaced by a kernel from another device.

DTBO is embedded into recovery's header-v1 payload. These scripts do not flash the separate phone DTBO partition.

Perseus should use the previously bootable V1.70 pair as requested. Device compatibility depends on the files you upload and subsequent hardware testing; a successful build does not establish boot compatibility.
