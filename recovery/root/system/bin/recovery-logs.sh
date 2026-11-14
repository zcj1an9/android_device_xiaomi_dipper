#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# One common export command on both independent device branches.
BASE=${RECOVERY_DIAG_BASE:-/tmp}
PSTORE=${RECOVERY_PSTORE_DIR:-/sys/fs/pstore}
PROC=${RECOVERY_PROC_DIR:-/proc}
OUT="$BASE/recovery-boot-logs"
SAVER=${RECOVERY_PSTORE_SAVER:-/system/bin/recovery-pstore-save.sh}
if [ ! -f "$OUT/snapshot.complete" ]; then
    sh "$SAVER" on-demand
fi
mkdir -p "$OUT/pstore-current" || exit 1
for file in "$PSTORE"/*; do
    [ -f "$file" ] || continue
    cp "$file" "$OUT/pstore-current/"
done
ls -lan "$PSTORE" > "$OUT/pstore-list-current.txt" 2>&1
[ ! -f "$BASE/recovery.log" ] || cp "$BASE/recovery.log" "$OUT/recovery.log"
dmesg > "$OUT/recovery-dmesg-current.txt" 2>&1
logcat -b all -d > "$OUT/recovery-logcat.txt" 2>&1
getprop > "$OUT/recovery-properties.txt" 2>&1
cat "$PROC/mounts" > "$OUT/recovery-mounts-current.txt" 2>/dev/null
ls -l /dev/block/bootdevice/by-name > "$OUT/block-links.txt" 2>&1
tar -czf "$BASE/recovery-boot-logs.tar.gz" -C "$BASE" recovery-boot-logs || exit 1
echo "$BASE/recovery-boot-logs.tar.gz"
