# SPDX-License-Identifier: Apache-2.0
# Hardware layout based on LucyfMorning/dipper and OrangeFox/device/dipper.
DEVICE_PATH := device/xiaomi/dipper
ifeq ($(wildcard $(DEVICE_PATH)/crypto-profile.mk),)
$(error Run tools/configure.py before lunch; the encryption profile must match the installed ROM)
endif
include $(DEVICE_PATH)/crypto-profile.mk

TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := kryo385
TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic
TARGET_2ND_CPU_VARIANT_RUNTIME := kryo385
TARGET_BOARD_PLATFORM := sdm845
TARGET_BOARD_PLATFORM_GPU := qcom-adreno630
TARGET_BOOTLOADER_BOARD_NAME := sdm845
TARGET_NO_BOOTLOADER := true
# Dipper has dedicated boot/recovery partitions, not A/B slots.
AB_OTA_UPDATER := false

BOARD_BOOT_HEADER_VERSION := 1
BOARD_BOOTIMG_HEADER_VERSION := 1
BOARD_KERNEL_BASE := 0x00000000
BOARD_KERNEL_PAGESIZE := 4096
BOARD_RAMDISK_OFFSET := 0x01000000
BOARD_KERNEL_TAGS_OFFSET := 0x00000100
BOARD_MKBOOTIMG_ARGS += --header_version 1 --ramdisk_offset 0x01000000 --tags_offset 0x00000100
BOARD_KERNEL_IMAGE_NAME := Image.gz-dtb
TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilt/Image.gz-dtb
BOARD_KERNEL_CMDLINE := console=ttyMSM0,115200n8 earlycon=msm_geni_serial,0xA84000 androidboot.hardware=qcom androidboot.console=ttyMSM0 androidboot.usbcontroller=a600000.dwc3 ehci-hcd.park=3 msm_rtb.filter=0x237 service_locator.enable=1 swiotlb=2048 loop.max_part=7 androidboot.configfs=true androidboot.boot_devices=soc/1d84000.ufshc androidboot.selinux=permissive

# No fixed userdata/system/vendor sizes: this phone has resized partitions.
BOARD_FLASH_BLOCK_SIZE := 262144
BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 67108864
BOARD_HAS_LARGE_FILESYSTEM := true
# SAR mount layout is described by recovery.fstab; this build flag was removed in Android 16.
TARGET_COPY_OUT_VENDOR := vendor
BOARD_ROOT_EXTRA_FOLDERS := bluetooth dsp firmware persist metadata
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true
TARGET_USES_MKE2FS := true
BOARD_SUPPRESS_SECURE_ERASE := true
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/recovery/recovery.fstab
TARGET_RECOVERY_PIXEL_FORMAT := BGRA_8888
TARGET_RECOVERY_DEVICE_DIRS += $(DEVICE_PATH)
BUILD_BROKEN_ELF_PREBUILT_PRODUCT_COPY_FILES := true

TW_THEME := portrait_hdpi
TW_Y_OFFSET := 87
TW_H_OFFSET := -87
TW_EXTRA_LANGUAGES := true
TW_INPUT_BLACKLIST := "hbtp_vm"
TW_BRIGHTNESS_PATH := "/sys/class/backlight/panel0-backlight/brightness"
TW_MAX_BRIGHTNESS := 2047
TW_DEFAULT_BRIGHTNESS := 511
# Install the core USB module with dipper's contents (see tools/build.sh).
TW_EXCLUDE_DEFAULT_USB_INIT := false
TW_INCLUDE_REPACKTOOLS := true
TW_INCLUDE_RESETPROP := true
TW_INCLUDE_LIBRESETPROP := true
# Read the real gauge instead of the health HAL's synthetic 100% fallback.
TW_CUSTOM_BATTERY_PATH := "/sys/class/power_supply/battery"
TW_USE_LEGACY_BATTERY_SERVICES := true
RECOVERY_SDCARD_ON_DATA := true
BOARD_HAS_NO_REAL_SDCARD := true
TARGET_RECOVERY_QCOM_RTC_FIX := true
# crypto-profile.mk selects crypto for the actual build mode. Do not override
# storage mode's false values here: this would re-enable FBE/keystore waits.
TWRP_INCLUDE_LOGCAT := true
TARGET_USES_LOGD := true
# Do not exclude APEX or override platform/security patch versions with 2099.


# Embed only Dipper's user-supplied DTBO; do not flash the phone DTBO partition.
BOARD_INCLUDE_RECOVERY_DTBO := true
BOARD_PREBUILT_DTBOIMAGE := $(DEVICE_PATH)/prebuilt/dtbo.img
