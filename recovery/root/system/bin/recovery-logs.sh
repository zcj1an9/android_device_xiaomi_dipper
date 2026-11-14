#!/system/bin/sh
out=/tmp/recovery-diagnostics
mkdir -p "$out"
cp /tmp/recovery.log "$out/" 2>/dev/null
dmesg > "$out/dmesg.txt" 2>&1
getprop > "$out/properties.txt"
cat /proc/mounts > "$out/mounts.txt"
ls -l /dev/block/bootdevice/by-name > "$out/blocks.txt" 2>&1
logcat -b all -d > "$out/logcat.txt" 2>&1
tar -czf /tmp/recovery-diagnostics.tar.gz -C /tmp recovery-diagnostics
echo /tmp/recovery-diagnostics.tar.gz
