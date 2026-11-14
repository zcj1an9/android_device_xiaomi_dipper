# Dipper prebuilts

Upload Dipper's `dtbo.img` here using `python3 tools/import-dtbo.py /path/dtbo.img`.
The existing pinned Dipper kernel and common crypto-blob fetch process is preserved.
Only the DTBO is new and awaiting upload. No other device DTBO is accepted as a fallback.
DTBO is embedded into the header-v1 recovery; no phone partition is flashed by these scripts.
Workflow is now manual-only. This source change has not been built or tested on hardware.
