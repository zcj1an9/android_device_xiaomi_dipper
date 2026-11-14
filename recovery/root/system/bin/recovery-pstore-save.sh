#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Snapshot the previous boot records exposed by this recovery's running kernel.
# Never erase pstore or change ramoops parameters. Kernel/DTB layout is external.
BASE=${RECOVERY_DIAG_BASE:-/tmp}
PSTORE=${RECOVERY_PSTORE_DIR:-/sys/fs/pstore}
PARAMS=${RECOVERY_RAMOOPS_PARAMS:-/sys/module/ramoops/parameters}
PROC=${RECOVERY_PROC_DIR:-/proc}
OUT="$BASE/recovery-boot-logs"
LOCK="$BASE/.recovery-pstore-save.lock"
[ -f "$OUT/snapshot.complete" ] && exit 0
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
mkdir -p "$OUT/pstore-early" || exit 1
{
    echo "capture_stage=${1:-on-demand}"
    echo 'These records are only what the running recovery kernel exposes.'
    echo 'An empty snapshot does not prove the previous kernel did not crash.'
    echo 'A userspace snapshot cannot correct incompatible kernel/DTB layouts.'
    date -u 2>/dev/null
    uname -a
    cat "$PROC/uptime" 2>/dev/null
} > "$OUT/capture-info.txt"
cat "$PROC/cmdline" > "$OUT/recovery-cmdline.txt" 2>/dev/null
cat "$PROC/mounts" > "$OUT/recovery-mounts-early.txt" 2>/dev/null
{
    for key in mem_address mem_size record_size console_size pmsg_size ftrace_size ecc mem_type; do
        printf '%s=' "$key"
        if [ -r "$PARAMS/$key" ]; then
            cat "$PARAMS/$key"
        else
            echo unavailable
        fi
    done
} > "$OUT/recovery-ramoops-params.txt"
if [ -z "${RECOVERY_PSTORE_DIR:-}" ]; then
    mkdir -p "$PSTORE"
    # Mount only if pstore is not already mounted at this path.
    if ! awk -v target="$PSTORE" '$2 == target && $3 == "pstore" {found=1} END {exit !found}' "$PROC/mounts"; then
        mount -t pstore pstore "$PSTORE" > "$OUT/pstore-mount.txt" 2>&1
    fi
fi
ls -lan "$PSTORE" > "$OUT/pstore-list-early.txt" 2>&1
count=0
for file in "$PSTORE"/*; do
    [ -f "$file" ] || continue
    if cp "$file" "$OUT/pstore-early/"; then count=$((count + 1)); fi
done
echo "$count" > "$OUT/pstore-file-count.txt"
if [ -r "$PROC/last_kmsg" ]; then
    cat "$PROC/last_kmsg" > "$OUT/last_kmsg.txt"
fi
dmesg > "$OUT/recovery-dmesg-early.txt" 2>&1
echo complete > "$OUT/snapshot.complete"
exit 0
