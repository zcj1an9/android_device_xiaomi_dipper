#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Run as root in an existing recovery. Output is text on stdout; no key material.
set -u
PROBE=/tmp/dipper-crypto-probe-$$
ACTIVE=
cleanup() {
    for target in $ACTIVE; do umount "$target" 2>/dev/null; done
    rmdir "$PROBE/vendor" "$PROBE/system" "$PROBE" 2>/dev/null
}
trap cleanup EXIT HUP INT TERM
mkdir -p "$PROBE/vendor" "$PROBE/system"
printf '\n=== RECOVERY KERNEL ===\n'
uname -a
printf '\n=== SELECTED RECOVERY PROPERTIES (not ROM properties) ===\n'
for key in ro.crypto.state ro.crypto.type ro.crypto.volume.options ro.crypto.volume.filenames_mode ro.crypto.metadata.enabled ro.crypto.dm_default_key.options_format.version ro.boot.dynamic_partitions ro.boot.dynamic_partitions_retrofit; do
    printf '%s=%s\n' "$key" "$(getprop "$key")"
done
printf '\n=== BLOCK LINKS ===\n'
for base in /dev/block/by-name /dev/block/bootdevice/by-name; do
    for part in system vendor cust logdump metadata userdata super; do
        ls -l "$base/$part" 2>/dev/null
    done
done
printf '\n=== CURRENT MOUNTS ===\n'
cat /proc/mounts
for part in vendor system; do
    dev=/dev/block/bootdevice/by-name/$part
    [ -e "$dev" ] || dev=/dev/block/by-name/$part
    target=$PROBE/$part
    if mount -t ext4 -o ro,noload "$dev" "$target" 2>/dev/null || mount -t erofs -o ro "$dev" "$target" 2>/dev/null; then
        ACTIVE="$target $ACTIVE"
        printf '\n=== %s READ-ONLY PROBE ===\n' "$part"
        for file in "$target"/build.prop "$target"/system/build.prop "$target"/etc/build.prop; do
            [ -f "$file" ] || continue
            echo "--- $part:${file#"$target"}"
            sed -n '/^ro\.build\.version\./p; /^ro\.vendor\.build\.security_patch=/p; /^ro\.vndk\.version=/p' "$file"
        done
        if [ "$part" = vendor ]; then
            for file in "$target"/etc/fstab*; do
                [ -f "$file" ] || continue
                echo "--- vendor:${file#"$target"}"
                cat "$file"
            done
            for file in "$target"/etc/vintf/manifest.xml "$target"/etc/vintf/manifest/*.xml "$target"/etc/init/*keymaster*.rc "$target"/etc/init/*keymint*.rc "$target"/etc/init/*gatekeeper*.rc; do
                [ -f "$file" ] || continue
                echo "--- vendor:${file#"$target"}"
                cat "$file"
            done
        fi
    else
        echo "Cannot probe $part read-only (already mounted, logical partition, or unsupported filesystem)."
    fi
done
printf '\n=== EXISTING DATA POLICY (no mount/unlock attempted) ===\n'
if command -v fscryptpolicyget >/dev/null 2>&1; then
    for target in /data /data/media /data/media/0; do
        fscryptpolicyget "$target" 2>&1
    done
else
    echo 'fscryptpolicyget unavailable in this recovery'
fi
printf '\n=== END ===\n'
