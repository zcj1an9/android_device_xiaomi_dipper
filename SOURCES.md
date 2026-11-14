# Sources and decisions

Core/tooling baseline: https://github.com/zcj1an9/android_device_xiaomi_dipper/commit/aee2411485463c7f3389a40caf95f7404ef2b240
Device reference: https://github.com/TeamWin/android_device_xiaomi_equuleus/tree/1e9ac6ba13a2358fe06b93faae654f442810efb0
TWRP core: TWRP-Test/android_bootable_recovery @ 8a58fc3b586b8a908337fa87529cfbbb119ec7bb
Vold: TWRP-Test/android_system_vold @ e7e26ed2ffd9ad0469a05515cfd91940a3366d19
Perseus binary reference SHA256: cf3b6b124faeb5c1087cbe364db40dd99ecb0ffba6c8ad2bb75e7ff42c0fd120

Only shared core fixes/build tooling are reused. Device layout, display values and USB rules are independent.
No hardcoded userdata/system partition sizes are carried over from another ROM.
MultiROM/logical/Super assumptions and 2099 security patches in reference trees are intentionally excluded.
Header v1 embeds each device's own DTBO at the user's request. Equuleus boot compatibility awaits its supplied binaries and device testing.
