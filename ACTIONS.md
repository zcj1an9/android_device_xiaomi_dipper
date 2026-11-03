# GitHub Actions 构建

工作流：**Build dipper TWRP**，位于 `.github/workflows/build-recovery.yml`。
源码固定从本仓库 `twrp-16.0` 分支读取；默认分支也放置同一工作流，以便显示 Run workflow。

## 触发

- 提交构建脚本、设备配置或 Recovery 文件到 `twrp-16.0`：自动编译 diagnostic 镜像。
- 手动运行：进入仓库 Actions → Build dipper TWRP → Run workflow，选择 mode 和编译并行数。
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
