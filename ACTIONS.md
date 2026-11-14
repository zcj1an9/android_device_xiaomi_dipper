> Direct upload mode: `prebuilt/Image.gz-dtb` and `prebuilt/dtbo.img` are used as uploaded. No hash/format checks or import-manifest registration are required. Workflows remain manual-only.

# GitHub Actions 构建

工作流：**Build dipper TWRP**，位于 `.github/workflows/build-recovery.yml`。
源码固定从本仓库 `twrp-16.0` 分支读取；默认分支也放置同一工作流，以便显示 Run workflow。

## 触发

- 提交构建脚本、设备配置或 Recovery 文件到 `twrp-16.0`：自动编译 storage 镜像。
- 手动运行：进入仓库 Actions → Build dipper TWRP → Run workflow，选择 mode 和编译并行数。
- `storage`（默认）：普通挂载未加密 data；适用于本机 fstab 未配置文件/metadata 加密且用户目录 fscryptpolicyget 均为 No policy set 的情况，不启动硬件解密服务。
- `diagnostic`：不需要 crypto_profile；不挂载 data/metadata，不启动硬件密钥服务。用于先验证 Recovery 能否启动、显示、使用 ADB。其二进制仍编译解密模块，以发现相关构建错误；不是可解密 data 的成品。
- `decrypt`：必须填写真实 ROM 的加密参数 JSON；缺少必填字段或有冲突时，在下载大体积源码前停止。

## crypto_profile

以下仅说明 JSON 格式，**示例值不是你的手机已确认值**：

```json
{
  "keymaster": 4,
  "policy": 2,
  "fileencryption": "aes-256-xts:aes-256-cts:v2",
  "os_version": "17",
  "security_patch": "2026-10-05",
  "vendor_patch": "2021-08-01",
  "metadata_partition": "logdump"
}
```

只有实际 fstab 使用 metadata encryption 时，再加 `metadata_encryption`、`keydirectory` 和 `dm_options_version`。确实没有 metadata 分区则设 `metadata_partition` 为 `none`。旧式单独的 wrappedkey 标志对应布尔值 `wrapped_key`。旧 `ice` 缩写不能直接交给现代 libfscrypt，需要先确认实际 cipher/policy。

JSON 作为环境变量传入，由 Python 转为参数列表执行，不会当作 shell 代码运行。

## 产物和排错

成功后在该次运行的 **Artifacts** 下载 `twrp-dipper-<mode>-<编号>`，内有镜像、SHA256SUMS、device-tree commit、crypto profile、源码版本快照和依赖哈希。

无论成功失败都会尝试上传 `dipper-build-logs-<编号>`，保留 14 天。失败请提供 `build-console.log` 或 `source-sync.log`。尚未编译成功前，不应把工作流存在等同于可用镜像。

工作流使用 Ubuntu 24.04 runner，清理其临时环境中未用于本次构建的 Android SDK、.NET、GHC、Swift、CodeQL、PowerShell、Azure CLI，创建 24 GiB swap，并检查可用磁盘。默认两个编译任务；Soong 的 Go 运行时设置 `GOMEMLIMIT=10GiB`、`GOGC=50`、`GOMAXPROCS=2`，降低内存峰值。GOMEMLIMIT 是 Go 运行时的软限制，不是整个构建进程的硬限制；这些设置不能保证避免内存不足或平台中断。

构建期间每 60 秒把可用内存、剩余 swap、磁盘和最高 RSS 进程写入 Action 日志及 `resource-usage.log`。正常退出或编译失败时还会保存 `runner-diagnostics.txt`。若整个运行器被关闭，artifact 上传仍可能无法执行，但已输出的资源记录可用于排查。编译步骤单独限制 300 分钟，给正常超时后的日志收集留出时间。

第三轮构建在 Soong 分析阶段收到 runner shutdown、退出 143，没有记录新的编译器报错；不能据此直接认定 OOM。本次调整是降低资源占用并增加证据，不是已确认根因的源码修复。

构建脚本按上游最小 manifest 要求设置 `ALLOW_MISSING_DEPENDENCIES=true`，以允许 Soong 扫描仍引用已裁剪模块的测试/模拟器项目。编译命令退出码、镜像存在和分区容量检查仍然有效；不忽略实际构建命令的失败。

diagnostic 镜像启动后可在电脑执行：

```powershell
adb shell sh /system/bin/dipper-crypto-info.sh > dipper-crypto-info.txt
adb shell sh /system/bin/dipper-recovery-logs.sh
adb pull /tmp/dipper-recovery-logs.tar.gz
```

crypto-info 也可以先在现有可用 Recovery 上运行，方法见 README。拿到真实参数后才能构建与现有 data 匹配的 decrypt 镜像；它仍需实机验证。

第五轮构建已通过 USB 安装规则检查并进入实际编译，但同步后只剩约 11 GiB，编译到约 47% 时空间不足 1 GiB，日志随后中断。CI 现在在保存 `dipper-source-lock.xml` 后删除临时 Android checkout 的 `.repo/project-objects` 和 `.repo/projects`，保留已签出的源码和 manifest，并要求至少 30 GiB 可用空间才开始编译；记录见 `disk-cleanup.log`。清理后的临时 checkout 不可继续 repo sync，后续任务必须重新同步。该清理仅在 GitHub Actions 的指定临时目录执行，不用于本地构建或设备树仓库。

## 分区挂载

三种模式共用静态分区布局：system、vendor、cust、cache、persist、firmware（modem）、dsp、bt_firmware（bluetooth）。Cust 独立挂到 /cust，不映射为 system_ext；若解密 profile 明确把 cust 用作 metadata，则只保留 /metadata，避免同一分区重复挂载。logdump 不会自动视作 metadata。

Cust、Persist、Firmware、DSP、Bluetooth Firmware 默认只读；ext4 的只读条目使用 noload。Cache 支持 ext4/F2FS。Boot、Recovery、DTBO 是镜像备份/恢复/刷写入口，不是文件系统挂载点。Cust 和 Cache 提供高级擦除入口；Persist、固件和 EFS 不提供擦除入口。不增加 formattable 或自动格式化配置。

Storage 模式使用普通 F2FS/ext4 data 挂载参数，不根据 Android 版本猜测加密选项；对有实际加密策略的其他 ROM，应选择 diagnostic 或提供真实 decrypt profile。挂载和镜像入口需要下一轮实机验证。

### 备份列表

- 文件备份：System、Vendor、Data（storage/decrypt 模式）、Cache、Cust、Persist、Firmware、DSP、Bluetooth Firmware。
- 镜像备份：Boot、Recovery、DTBO、System Image、Vendor Image、Cust Image、Persist Image、Modem Firmware Image。
- Modem 镜像组包含 modem、bluetooth、dsp；EFS 镜像组包含 modemst1、modemst2、fsc、fsg，分区名称参考 TeamWin 的 dipper 设备树。
- Persist、EFS、Modem 的镜像入口不加入普通镜像刷写列表，但可通过备份恢复流程恢复。只有实际存在的分区才能完成备份。
- 文件备份和 Image 是同一分区的两种备份形式，无需默认全选。Data 文件备份沿用 TWRP 行为，不包含 /data/media 的内部存储文件；照片/下载文件需另行复制。

### EROFS

System、Vendor、Cust 均同时提供 ext4 与 EROFS 挂载条目；EROFS 按只读挂载，不作为可写文件系统使用。明确打包 fsck.erofs、dump.erofs、mkfs.erofs 的 Recovery 变体。可用文件备份保存分区内容，也可用 System/Vendor/Cust Image 保存原始镜像；更新 EROFS 内容应刷写新镜像。Data/Cache 继续使用 F2FS/ext4。是否能挂载某个 EROFS 镜像还取决于该镜像使用的压缩算法和内核支持的格式特性。

## 设置持久保存与普通存储启动

核心的 TWRP 设置路径改为 `/cache/TWRP/.twrp_settings`，读写前必须成功挂载 Cache，写入失败会返回错误并记录日志。清空 Cache 会重置 TWRP 设置。此调整不写 Persist 中的校准文件。

Storage 模式明确关闭 TW_INCLUDE_CRYPTO/TW_INCLUDE_CRYPTO_FBE，设备 BoardConfig 不再覆盖生成的模式选项；keystore2.recovery 由解密核心按需引入，不再额外强制引入普通 keystore2。这避免未加密 data 被带入 FBE 初始化和 keystore2 等待。Decrypt 模式继续启用硬件解密流程。

Advanced Wipe 增加 System、Vendor、Cust，并显式保留 Cache、Data；System flags 使用核心归一化后的 /system_root 路径，同时修正 System 文件备份开关。适用于实际 ext4/F2FS 文件系统。EROFS 不能按可写目录擦除，应通过对应 Image 刷写新镜像。DTBO、EFS、Persist 和固件仍仅提供各自的备份/恢复/镜像操作。

