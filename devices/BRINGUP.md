# equuleus / perseus 首轮独立硬件构建

工作流：`.github/workflows/build-other-recoveries.yml`，分支 `recovery-next`。
一次启动两个独立 runner，fail-fast=false。dipper 的 `twrp-16.0` 构建线不变。

共享核心及工具固定在 dipper 已成功构建的 aee2411485463c7f3389a40caf95f7404ef2b240。
硬件输入固定版本与每个文件的 Git blob 哈希见 `bringup-targets.json`。
`tools/prepare-other-device.py` 生成完整设备树，并校验实际检出的 commit 和硬件文件。

| 设备 | 硬件来源 | 屏幕 | 亮度上限 | 内核位置 |
|---|---|---|---|---|
| equuleus，Mi 8 Pro | TeamWin/android_device_xiaomi_equuleus android-10 固定提交 | 1080×2248 | 1023 | Image.gz-dtb |
| perseus，Mi MIX 3 | TeamWin/android_device_xiaomi_perseus android-9.0 固定提交 | 1080×2340 | 2047 | prebuilt/Image.gz-dtb |

每台使用自己的内核、USB init、屏幕参数、上游分区路径及文件系统类型。
这不是将 dipper 的内核或镜像改名。共享的是经过构建验证的 Android 16 TWRP 核心、
设置保存、真实电池路径、运行时修复、ZC_J1an9 启动介绍及四秒启动停留。

## 本轮范围

首轮为 bringup 镜像，验证内核启动、屏幕、触摸、ADB/MTP、真实电量和 cache 设置保存。
没有确认这两台安装 ROM 的 data 加密策略；所以不生成 userdata 挂载/解密配置，
不启动供应商 crypto HAL，不暴露擦除/刷写入口。cache 可写用于 TWRP 设置；其他
已知文件系统以只读方式挂载。并不宣称 Android 17 解密或全部 dipper 功能已验证。

保留上游 64 MiB recovery 分区限制、4096 页大小及 header v0；equuleus 采用上游
LZMA ramdisk 配置。镜像打包后必须检查非空且不超过 64 MiB，失败不上传镜像。
现代 EROFS 用户空间工具可以被编入，但是否能挂载还取决于各设备预编译内核，
不把工具存在当成内核已经支持该文件系统。

## perseus 的 DTBO

已解析上游 Image.gz-dtb，附带三份 SDM845 v1/v2/v2.1 SoC 基础 DTB，
并确认内核 CONFIG_BUILD_ARM64_DT_OVERLAY=y。设备配置依赖匹配的外部 DTBO。
上游设备树没有提供 dtbo.img；不能随意拿 dipper 或 4.19 test 的 DTBO 代替。
本次不设置 BOARD_PREBUILT_DTBOIMAGE，也不打包 recovery DTBO，不写手机 DTBO 分区。
因此编译成功仍不能证明与手机当前 DTBO 兼容。真机启动前应备份现有 recovery/boot/dtbo，
并核对当前 dtbo.img 与本次 TeamWin 设备内核的配套性；优先使用 bootloader 支持的
临时 fastboot boot 测试，不把“没有改 DTBO”误当成“DTBO 一定兼容”。

## 产物

- `twrp-<device>-bringup.img`
- SHA256SUMS、DEVICE_PROVENANCE.json、crypto-profile.json
- 固定源码清单、上游 BoardConfig/fstab 参考及完整生成设备树源码压缩包
- 各机型独立编译日志

设备真机测试尚未完成；老的 targets.json 保持 validation=pending，避免伪造已验证状态。
本工作流直接执行明确的 bringup 矩阵，不经过正式 storage/decrypt 验证入口。

## 4.19-only 更新

两台内核均从 zcj1an9/android_kernel_xiaomi_sdm845_419 的稳定 test 提交
49f75ba72af749092196b29348b98dbd1d8a19eb 编译，使用 LLVM/Clang 14 和每台自己的 config。
三个既有外部依赖只在一次性 CI 内核目录同步到固定提交，不添加到内核 GitHub 仓库。
TeamWin 树只提供硬件参数、USB 及分区参考，其旧预编译内核不进入产物。
准备脚本会检查内核 gzip 内容中的 Linux 4.19 版本、设备名称、源码提交和 SHA256；
缺少有效 4.19 内核时停止，不回退到旧内核。
perseus 保留 DT_OVERLAY 方案，生成的六份设备 overlay 及源码随镜像保存。
本次仍不写手机 DTBO，也不根据猜测的板号制作可刷 DTBO 表；应与手机现有 DTBO 核对。
