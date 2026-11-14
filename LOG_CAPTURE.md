# dipper boot-failure log capture

This device branch snapshots the pstore records exposed by the running recovery kernel during init `post-fs`, before the recovery main UI starts. It preserves that initial copy when you export logs later. Nothing deletes pstore, changes sysfs parameters, flashes a partition or reformats data. Logs stay in `/tmp`; export before rebooting.

## Kernel and DTB prerequisite

The ramoops memory layout is defined by the prebuilt kernel and its DTB, not TWRP userspace. Rebuilding the ramdisk alone cannot correct an incompatible kernel layout. Use this device's own `prebuilt/Image.gz-dtb` and `prebuilt/dtbo.img` matching the Android test you want to diagnose. Uploaded files are used directly, without binary validation or replacement. This change does not modify the Android kernel test/A17 branches or patch supplied binaries.

The examined Dipper V1.73 test DTBs declare address 0xB0000000, total size 4194304, record size 262144, console size 262144, ftrace size 262144, and pmsg size 2097152. The earlier Dipper recovery instead exposed record size 0 and console size 2097152. This is a Dipper reference, not a verified Equuleus runtime layout. Check each device's exported runtime parameters independently; DTBO overlays may affect the final runtime tree.

## Capture

1. After the new recovery itself has been boot-tested, reproduce the Android boot failure once and promptly enter recovery without starting another OS.
2. From the computer, run these commands in order:

```sh
adb shell sh /system/bin/recovery-logs.sh
adb pull /tmp/recovery-boot-logs.tar.gz
```

The archive includes `pstore-early/`, `pstore-current/`, the actual recovery ramoops parameters, capture stage, command line, mounts, recovery log, dmesg and recovery logcat. `capture_stage=on-demand` means no automatic early snapshot was available. Recovery dmesg/logcat are labeled separately from previous-boot pstore records. Empty pstore still exports diagnostic metadata and is not proof that the failed kernel did not crash.

Kernel initialization and the bootloader may already have overwritten prior records before userspace starts. The early copy reduces later userspace loss; it cannot undo that or repair mismatched layouts.

## Validation

Run `python3 tests/test_recovery_log_capture.py` on the host. It uses temporary fake proc/sysfs directories to test early capture, preservation after pstore contents change, archive contents, parameters and empty pstore. Shell syntax and this fixture test pass; no full TWRP build or device validation was performed by this source update.
