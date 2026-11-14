# SPDX-License-Identifier: Apache-2.0
LOCAL_PATH := device/xiaomi/perseus
PRODUCT_SHIPPING_API_LEVEL := 28
TARGET_SCREEN_HEIGHT := 2340
TARGET_SCREEN_WIDTH := 1080
PRODUCT_PACKAGES += resetprop logcat logd task_profiles.json.recovery
PRODUCT_PACKAGES += fsck.erofs.recovery dump.erofs.recovery mkfs.erofs.recovery
TARGET_RECOVERY_DEVICE_MODULES += libion
RECOVERY_LIBRARY_SOURCE_FILES += $(TARGET_OUT_SHARED_LIBRARIES)/libion.so
PRODUCT_COPY_FILES += $(filter-out %:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.usb.rc,$(call find-copy-subdir-files,*,$(LOCAL_PATH)/recovery/root/,$(TARGET_COPY_OUT_RECOVERY)/root/))
include $(LOCAL_PATH)/crypto-profile.mk
