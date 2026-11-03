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

工作流使用 Ubuntu 24.04 runner，只清理其临时环境中的 Android SDK、.NET、GHC、Swift，创建 8 GiB swap，并检查可用磁盘。完整源码及构建若超出免费 runner 资源，任务会失败并保留已有日志；不保证该源码版本一定能在托管 runner 上完成。

diagnostic 镜像启动后可在电脑执行：

```powershell
adb shell sh /system/bin/dipper-crypto-info.sh > dipper-crypto-info.txt
adb shell sh /system/bin/dipper-recovery-logs.sh
adb pull /tmp/dipper-recovery-logs.tar.gz
```

crypto-info 也可以先在现有可用 Recovery 上运行，方法见 README。拿到真实参数后才能构建与现有 data 匹配的 decrypt 镜像；它仍需实机验证。
