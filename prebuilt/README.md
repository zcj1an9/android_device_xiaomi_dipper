# equuleus prebuilts

Place this device's `Image.gz-dtb` and `dtbo.img` here. Files are not shared across branches.
Import with `python3 tools/import-prebuilts.py --kernel /path/Image.gz-dtb --dtbo /path/dtbo.img`.
The importer checks gzip, Linux 4.19, appended DTBs, DTBO bounds and pinned hashes before writing anything.
Perseus is pinned to the previously bootable V1.70 pair; no V1.73 substitution.
Binary files are pending upload. No automatic download or Dipper kernel fallback is allowed.
DTBO is embedded in recovery's header-v1 payload; this project does not flash the phone DTBO partition.
