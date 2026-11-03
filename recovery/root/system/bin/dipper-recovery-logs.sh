#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Recovery logs only. Previous Android logcat is volatile unless previously saved.
set -eu
OUT=/tmp/dipper-recovery-logs
mkdir -p "$OUT/pstore"
cp /tmp/recovery.log "$OUT/" 2>/dev/null || true
dmesg > "$OUT/dmesg.txt" 2>&1 || true
logcat -b all -d > "$OUT/recovery-logcat.txt" 2>&1 || true
cat /proc/mounts > "$OUT/mounts.txt"
for key in init.svc.dipper-qseecomd init.svc.dipper-keymaster init.svc.dipper-gatekeeper init.svc.keystore2 dipper.crypto.ready ro.crypto.state ro.crypto.type twrp.all.users.decrypted; do
    printf '%s=%s\n' "$key" "$(getprop "$key")"
done > "$OUT/crypto-services.txt"
if [ -d /sys/fs/pstore ]; then
    for file in /sys/fs/pstore/*; do
        [ -f "$file" ] && cp "$file" "$OUT/pstore/" || true
    done
fi
tar -czf /tmp/dipper-recovery-logs.tar.gz -C /tmp dipper-recovery-logs
echo /tmp/dipper-recovery-logs.tar.gz
