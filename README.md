> Direct upload mode: `prebuilt/Image.gz-dtb` and `prebuilt/dtbo.img` are used as uploaded. No hash/format checks or import-manifest registration are required. Workflows remain manual-only.

# TWRP device tree for Xiaomi Mi 8 (dipper)

仓库建议命名：`android_device_xiaomi_dipper`；分支：`twrp-16.0`；Android 源码内路径：`device/xiaomi/dipper`。

**状态：实验性源码适配，尚未完成 Android 全量编译及实机解密验证。不能把本树视为已验证的 Android 17 解密 Recovery。**

GitHub Actions 自动/手动编译、诊断版和解密参数输入说明见 [ACTIONS.md](ACTIONS.md)。

硬件基础来自 OrangeFox 的 dipper / sdm845-common；解密核心使用 TWRP-Test 的 Android 16 分支。该核心含现代 synthetic-password、keystore2 和 HIDL Gatekeeper 路径，但实际 Android 17 ROM 的 protector 格式、TEE、Keymaster blob、fscrypt policy 仍必须匹配。上游 manifest README 主要面向 Weaver/OMAPI 设备，本树针对 dipper 的非 Weaver 高通路径仍需实机验证。不是 Fox 12.1 设备树的直接替换品。

## 范围

- dipper 专用 4.19 内核；64 MiB recovery；boot header v1；1080×2248 屏幕。
- 静态分区，兼容改过 system/vendor 容量的设备；不写死 userdata/system/vendor 容量。
- ext4 / f2fs data；ext4 / EROFS system 和 vendor。
- 按实际 ROM 生成 Keymaster 3.0 或 4.0 配置，只启动一套服务。
- 按实际参数选择 fscrypt v1/v2、metadata 分区、metadata cipher/keydirectory。
- 不采用 PixelExperience 名称识别、不导入 Fox 自动切换分区脚本、不把安全补丁时间设为 2099。
- 构建前要求显式生成加密配置，不把 VNDK 版本或 Android 版本当作加密格式。

不支持改造动态分区、FDE、KeyMint/AIDL-only 硬件方案。如果采集结果显示这些情况，需要进一步适配。现有 Keymaster/Gatekeeper 二进制来自上游公共树，不能保证与所有移植 vendor 的 TEE 密钥相容。没有加入 KSU/SUSFS 或现有 test 内核源码，也没有改写手机分区的初始化脚本。

## 1. 先采集实际 ROM 的加密信息

在当前能进入的 TWRP 下，在电脑 PowerShell 执行（不是在手机 adb shell 中再执行 adb）：

```powershell
adb push tools/collect-crypto-info.sh /tmp/collect-crypto-info.sh
adb shell sh /tmp/collect-crypto-info.sh > dipper-crypto-info.txt
```

脚本只读探测静态 system/vendor；不挂载或解锁 data，不读取密钥内容。ext4 使用 `ro,noload`，防止 journal replay。打印 recovery 属性时会标注来源；配置时应使用从 ROM build.prop 读取的版本/补丁时间，不能拿 recovery 自身的值代替。若 vendor 已被挂载或为逻辑分区，探测可能失败，需要直接提供 ROM 中的 `vendor/etc/fstab*`、Keymaster/KeyMint/Gatekeeper 的 VINTF manifest 和 init rc。

确认以下信息再生成配置：

| 参数 | 来源 |
|---|---|
| Keymaster 3 或 4 | vendor HAL manifest、服务 rc、实际服务/库 |
| fscrypt policy 1 或 2 | 已有 data policy 与实际 fstab；不能仅凭 Android 17 推断 |
| fileencryption | ROM fstab 中该项完整值，包含 wrappedkey/inlinecrypt 等选项 |
| metadata 分区 | 实际 fstab；本机曾使用 logdump，但不能据此推断所有 ROM |
| metadata_encryption / keydirectory | 只有 ROM fstab 存在时才启用，必须成对提供 |
| OS / system SPL / vendor SPL | 正在使用的 ROM build.prop |

老 fstab 的 `fileencryption=ice` 不能直接当成现代 libfscrypt 的 cipher token。工具会拒绝该缩写；需要确认真实 cipher、policy 和硬件 wrapped-key 行为，不能盲目替换成 AES-XTS。

## 2. 获取源码和预编译依赖

Linux 主机需要 git、Python 3、Android repo 和 AOSP 构建依赖。建议使用独立源码目录；RAM/磁盘需求取决于同步范围和并行度，完整构建通常需要远多于设备树本身的空间。

本仓库只管理设备配置和脚本。预编译内核/高通库从固定的上游提交获取，并通过 `PREBUILTS.sha256` 校验：

```bash
# 本仓库放在 /work/android_device_xiaomi_dipper，Android 源码放在 /work/twrp。
cd /work/android_device_xiaomi_dipper
bash tools/fetch-prebuilts.sh
bash tools/sync-source.sh /work/twrp
```

manifest 和 recovery/vold 固定版本见 `SOURCES.md` 与 `manifests/dipper-core.xml`。其他上游项目仍跟随 manifest 中的分支；同步后会保存完整的 `dipper-source-lock.xml`，便于记录本次构建实际使用的版本。

## 3. 生成手机专用配置

下面**只是参数格式示例，不是本机已确认参数**。日期也必须换成 ROM 实际值：

```bash
python3 tools/configure.py \
  --keymaster 4 --policy 2 \
  --fileencryption 'aes-256-xts:aes-256-cts:v2' \
  --os-version 17 \
  --security-patch 2026-10-05 --vendor-patch 2021-08-01 \
  --metadata-partition logdump
```

只有实际 fstab 包含 metadata encryption 时，才再加入例如：

```text
--metadata-encryption aes-256-xts --keydirectory /metadata/vold/metadata_encryption --dm-options-version 2
```

不使用 metadata 分区时填写 `--metadata-partition none`。`--dm-options-version` 也必须与 ROM 的 `ro.crypto.dm_default_key.options_format.version` 匹配，不能照抄示例。只有旧 fstab 存在单独的 `wrappedkey` 标志时才加 `--wrapped-key`；现代 `wrappedkey_v0` 等应保留在真实的 fileencryption 字符串中。

工具生成 `crypto-profile.mk/json`、Recovery fstab、vold 默认 fstab、最小 HAL manifest、服务 rc 和 ROM 版本绑定属性。它只写本地设备树，不操作手机。没有默认加密 profile，是为了避免把未知参数作为设备事实发布。

## 4. 构建

```bash
cd /work/android_device_xiaomi_dipper
DIPPER_JOBS=4 bash tools/build.sh /work/twrp
```

脚本把设备树复制到 `/work/twrp/device/xiaomi/dipper`；若目标已有另一棵树则停止，避免覆盖。若已经把本仓库直接放在该路径，脚本会直接使用它。

默认 lunch：`twrp_dipper-bp2a-userdebug`，对应已检查的 TWRP-Test build 分支。自定义源码若使用其他 release config，可通过 `DIPPER_LUNCH` 明确覆盖。

这套最小 manifest 按[上游说明](https://github.com/TWRP-Test/platform_manifest_twrp_aosp/blob/814b553116ceedde197f70389cff9661d81d8337/README.md)要求启用 `ALLOW_MISSING_DEPENDENCIES=true`：未同步的测试/模拟器项目仍可能被其他 Android.bp 引用，不能在全局依赖扫描阶段就中止。该开关不代表镜像已经构建成功；脚本仍要求 `recoveryimage` 命令成功退出、镜像存在且不超过 recovery 分区大小。若实际构建目标继续报缺依赖，应修复对应依赖，不能用空模块替代。

脚本还移除 Recovery 自己的 keystore2 服务的 `critical` 标志，避免该实验服务反复崩溃时触发重启而失去 ADB；不改手机系统。产物：

```text
/work/twrp/out/target/product/dipper/recovery.img
/work/twrp/dipper-recovery-build.log
```

修改加密配置后，若设备树是由脚本复制进 Android 源码目录，需要手动移走旧副本后再构建；不要误用上一次的 profile。切换 policy 或核心版本时应使用干净的输出目录。

## 5. 实机测试和日志

先保留当前可用 Recovery。若 bootloader 支持，使用 `fastboot boot recovery.img` 临时启动测试。不要通过 Format Data、删除 locksettings/spblob/keystore 文件来“解决”解密失败；这不会修复兼容性。

在新 Recovery 中尝试一次解锁后，电脑执行：

```powershell
adb shell sh /system/bin/dipper-recovery-logs.sh
adb pull /tmp/dipper-recovery-logs.tar.gz
```

包含 recovery.log、Recovery 自身的 logcat、dmesg、服务状态以及现有 pstore 文件。**Recovery 的 logcat 不是上一次失败 Android 启动的 logcat**。解密后可以另行导出 `/data/tombstones`、`/data/anr`、`/data/system/dropbox`；过去的 logcat 必须由系统启动时预先保存，或在系统 adbd 可用时从电脑实时采集。

预编译内核启用 dm-default-key、inline encryption、binderfs；其配置没有启用 PSTORE_CONSOLE/PSTORE_PMSG，因此不能保证恢复你现有 test 内核的 ramoops console/pmsg。此适配未声明其 ramoops 布局兼容，需要保留上一份可读取 pstore 的 Recovery 作为排障工具。

## 当前验证边界

完成设备配置生成、配置冲突检查、脚本语法和依赖哈希检查；尚无完整 Android 构建或手机解密成功结果。编译成功也不能代替一次真实解锁验证，尤其要检查 DE 初始化、Gatekeeper auth token、keystore2 blob 解封装和 CE key 安装分别在哪一步失败。

## 普通存储与更多分区

本机采集的 userdata 为 F2FS，ROM fstab 未配置 fileencryption/metadata_encryption，媒体、用户和 CE/DE 目录均返回 No policy set。为此新增普通存储模式：

```bash
python3 tools/configure-diagnostic.py --mount-data
bash tools/build.sh /path/to/android-source
```

GitHub Actions 默认选择 `storage`。原 `diagnostic` 模式继续省略 data/metadata；`decrypt` 继续要求真实加密 profile。

共同增加 Cust、Persist、Firmware、DSP、Bluetooth Firmware 和 Cache 挂载入口，并提供 DTBO 镜像备份/恢复/刷写。DTBO 无法作为目录挂载。辅助固件分区默认只读，且不提供擦除入口；不修改分区大小。完整布局见 ACTIONS.md。

备份列表同时增加 System/Vendor/Cust/Persist 镜像、Modem 固件镜像组和 EFS（modemst1、modemst2、fsc、fsg）组。Data 文件备份不包含内部存储 /data/media，照片等文件请另行复制。详情见 ACTIONS.md。


## 启动画面署名与展示时间

GUI2 启动画面保留上游 Logo、实际版本和设备名称，在版本上方加入 `ZC_J1an9`。
正常启动进入主页前，启动画面至少展示 4 秒，再执行上游约 0.3 秒淡出动画；
如果初始化本来就超过 4 秒，不额外等待。解密、系统只读确认和脚本进度页面沿用上游流程。

本地和 CI 的 `tools/build.sh` 都会运行 `tools/fix-splash-branding.py`，
只对清单固定的 GUI2 源码应用补丁；可重复执行，遇到未识别的源码会在编译前停止。
没有添加 init sleep，也没有延迟后台的挂载、设置读取或服务初始化。

