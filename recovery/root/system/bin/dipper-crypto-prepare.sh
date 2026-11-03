#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Apply the actual installed ROM's keymaster OS binding in recovery RAM only.
# Never upgrade, delete or replace any /data key files.
setprop dipper.crypto.ready 0
if ! command -v resetprop >/dev/null 2>&1; then
    echo 'dipper: resetprop missing; hardware crypto startup stopped' >/dev/kmsg
    exit 1
fi
while IFS='=' read -r name value; do
    case "$name" in
        ro.build.version.release|ro.build.version.security_patch|ro.vendor.build.security_patch|ro.crypto.volume.options|ro.crypto.dm_default_key.options_format.version)
            [ -n "$value" ] || exit 1
            resetprop "$name" "$value" || exit 1
            ;;
    esac
done < /system/etc/dipper-crypto.prop
setprop dipper.crypto.ready 1
