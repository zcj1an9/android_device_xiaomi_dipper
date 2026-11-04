# 三机型开发与批量构建

开发分支为 `recovery-next`，从 dipper 的 `54a3e91` 修复版本开始。
`twrp-16.0` 保留现有 dipper 构建线，本轮不向它提交任何修改。

目标：一次工作流生成 dipper、perseus、equuleus 三个独立 job，最多同时使用
三个 runner；每个 job 使用自己设备的源码、内核、lunch、分区布局和产物目录。
不是把一个 dipper 镜像改名发给三个设备，也不是在一个输出目录连续覆盖编译。
一个编译 job 失败时，其他设备 job 继续完成，日志和镜像单独上传。

## 当前状态：只整理代码，不编译

- 本分支工作流删除 push/PR/schedule 触发，只保留手动入口。
- 手动入口 `execute` 默认 false，只输出计划，不同步 Android 源码、不创建编译 runner。
- `devices/targets.json` 中三个机型的 `build_enabled` 都是 false。
- 即使手动勾选 execute，只要任一请求机型未验证，整批会在下载源码前停止。
- dipper 待实机验证语言保存、启动等待、挂载、备份恢复和擦除入口。
- perseus、equuleus 是待适配条目，尚无确认的设备仓库、内核和分区参数。
  不填入推测的硬件信息，不复制 dipper 的加密参数。

查看当前计划只需要 Python 3.9+，不需要编译环境或网络：

```bash
python3 tools/plan-recoveries.py --devices dipper,perseus,equuleus --mode storage
python3 -m unittest discover -s tests
```

报告中的 ready=false 是当前预期状态。`--require-ready` 会在未就绪时返回失败。
计划采用整批检查，不会在请求三个机型时悄悄只编译 dipper。

## 后续接入顺序

1. 完善并验证 dipper。
2. 为 perseus/equuleus 分别确认设备树仓库与 ref、预编译内核及哈希、启动镜像头与
   分区容量、屏幕触摸、fstab/分区链接、真实 data 策略。
3. 各设备实现相同的构建工具接口，但保留各自硬件配置：
   `tools/ci-configure.py`、`sync-source.sh`、`ci-reclaim-space.sh`、`ci-build.sh`；
   提供 AndroidProducts.mk、PREBUILTS.sha256、crypto-profile.json 和
   `<device>-source-lock.xml`。编译日志命名为 `<device>-recovery-build.log`。
4. 同步/构建工具仍接受 DIPPER_JOBS、DIPPER_SYNC_JOBS、DIPPER_LUNCH 这组现有接口名；
   它们在每个独立 runner 内设置，lunch 值必须属于对应机型。后续可统一改成 RECOVERY 前缀。
5. 某个设备通过独立验证后，才填写自己的 modes、validation=passed 和 build_enabled=true。
   `storage` 只能用于已经确认普通 data 挂载参数的设备。
6. 三台全部就绪后，再启用批量编译入口：devices 选三个机型、execute=true、max_parallel=3。
   本轮不执行此步骤，也不把暂存工作流合并到默认分支。

不同设备可能需要不同 ROM 解密参数。批量流程暂不接受一份通用 decrypt profile；
当前 dipper 单设备解密配置工具仍保留，批量解密模式待设备参数确认后单独实现。

产物分别命名 `twrp-<device>-<mode>-<run>`，日志为 `<device>-build-logs-<run>`，
每个镜像附带设备源码 SHA、预编译哈希、manifest 锁定清单和镜像 SHA256。
