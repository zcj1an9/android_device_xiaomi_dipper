# Validation status

Checked in this workspace on 2026-11-03:

- Shell parser checks for all build, sync, fetch, probe and recovery-log scripts.
- Generated both a Keymaster 4 / policy v2 / metadata-encrypted configuration
  and a Keymaster 3 / policy v1 / no-metadata configuration.
- Parsed generated HAL XML; checked that exactly the selected Keymaster service
  is referenced, and that switching profiles removes stale metadata options.
- GNU Make parsed BoardConfig at the actual `device/xiaomi/dipper` path and
  resolved the fscrypt policy and prebuilt kernel path.
- Rejected conflicting policy/cipher versions and incomplete metadata parameters.
- Confirmed generated fstabs contain no `formattable` or dynamic `logical` flags.
- Verified local upstream prebuilts against PREBUILTS.sha256.

These are source/configuration checks, not a full Android build. No recovery.img
has been produced or tested on a phone. The supplied crypto parameter examples
are examples only; the phone's actual parameters have not yet been collected.
