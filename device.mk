# SPDX-License-Identifier: Apache-2.0
LOCAL_PATH := device/xiaomi/dipper
PRODUCT_SHIPPING_API_LEVEL := 27
TARGET_SCREEN_HEIGHT := 2248
TARGET_SCREEN_WIDTH := 1080
# Crypto builds obtain keystore2.recovery from the core's conditional deps.
PRODUCT_PACKAGES += resetprop logcat logd
# Include EROFS image inspection/creation tools explicitly in the recovery.
PRODUCT_PACKAGES += fsck.erofs.recovery dump.erofs.recovery mkfs.erofs.recovery
TARGET_RECOVERY_DEVICE_MODULES += libion
RECOVERY_LIBRARY_SOURCE_FILES += $(TARGET_OUT_SHARED_LIBRARIES)/libion.so
# The core's Soong prebuilt owns init.recovery.usb.rc. tools/build.sh supplies
# dipper's USB contents to that module; do not create a second Make install rule.
PRODUCT_COPY_FILES += $(filter-out %:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.usb.rc,$(call find-copy-subdir-files,*,$(LOCAL_PATH)/recovery/root/,$(TARGET_COPY_OUT_RECOVERY)/root/))
PRODUCT_COPY_FILES += $(LOCAL_PATH)/tools/collect-crypto-info.sh:$(TARGET_COPY_OUT_RECOVERY)/root/system/bin/dipper-crypto-info.sh
# Native recovery services (servicemanager, hwservicemanager and keystore2)
# come from the selected TWRP core. Only QTI hardware services are supplied here.
# The generated profile is also read here because product config precedes BoardConfig.
include $(LOCAL_PATH)/crypto-profile.mk
