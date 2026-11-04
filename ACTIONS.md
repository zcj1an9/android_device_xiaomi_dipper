# 多设备构建暂存流程

本分支 `recovery-next` 的工作流是 **Plan or build Xiaomi recoveries**，文件为 `.github/workflows/build-recovery.yml`。

当前只整理代码，不启动编译。`twrp-16.0` 的原 dipper 工作流不变。

## 一次触发、三个独立任务

目标设备：`dipper,perseus,equuleus`。工作流先运行计划检查，全部就绪后才可生成三个矩阵编译任务。任务各自使用独立 runner、设备树、内核、lunch、源码输出和缓存；最多三台并行。单个任务失败不会取消其他设备任务。

## 当前不会编译的原因

- 没有 push、pull_request 或 schedule 触发。
- 手动参数 execute 默认 false：只运行计划检查。
- devices/targets.json 中三个 build_enabled 均为 false，validation 均为 pending。
- perseus/equuleus 的未确认源码和硬件字段留空，没有套用 dipper 配置。
- 即使传 execute=true，也必须整批通过设备就绪检查，才开始同步和构建。

可在本地检查计划，不下载源码、不编译：

```bash
python3 tools/plan-recoveries.py --devices dipper,perseus,equuleus --mode storage
python3 -m unittest discover -s tests
```

当前 ready=false 是预期结果。设备状态和后续适配步骤见 [MULTI_DEVICE.md](MULTI_DEVICE.md)。暂存工作流本轮不会合并到 main，也不会启动或重跑任何编译。

## 后续就绪后的手动参数

| 参数 | 用途 |
| --- | --- |
| devices | 默认请求 dipper,perseus,equuleus |
| execute | 默认 false；全部适配验证完成后才用于实际编译 |
| mode | storage 或 diagnostic；每个设备必须单独确认支持 |
| max_parallel | 三个机型之间的并行数量，默认 3 |
| jobs | 每台独立 runner 内的编译并行数，默认 2 |

批量 decrypt 暂不开放：不同设备需要各自真实加密 profile。单设备解密配置工具保留。

产物分别为 twrp-<device>-<mode>-<run>，日志为 <device>-build-logs-<run>。镜像附带设备源码 SHA、manifest 版本锁定、预编译文件哈希和 SHA256SUMS。

dipper 的现有设置保存、普通 data 挂载、分区备份和 EROFS 功能继承自 54a3e91；仍需实机验收。清空 Cache 会重置 /cache/TWRP 中的 Recovery 设置。
