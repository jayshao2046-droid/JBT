# TASK-0043 data_scheduler 守护切换到 LaunchAgent

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0043 |
| 任务标题 | data_scheduler 守护切换到 LaunchAgent |
| 服务归属 | data |
| 执行 Agent | 数据 / Atlas |
| 优先级 | P1 |
| 来源 | TASK-0039 / ISSUE-DR4-001 |
| 状态 | ✅ A批完成并锁回 |

---

## 背景

1. `TASK-0039` DR4 演练确认：Mini 上的 `data_scheduler` 当前以 `nohup python -m services.data.src.scheduler.data_scheduler --daemon` 裸进程方式运行，`kill -9` 后不会自动恢复。
2. Mini 机器历史上曾存在 `~/Library/LaunchAgents/com.botquant.data_scheduler.plist`，但当前已被禁用，说明 LaunchAgent 方案在该设备上有已验证先例。
3. `services/data/src/main.py` 的 `ops/restart-collector` 已把 `data_scheduler` 映射到 `com.botquant.data_scheduler`，因此修复方案应保持该 label 不变，以免破坏现有运维接口语义。

---

## 白名单冻结

| 文件 | 操作 | 说明 |
|------|------|------|
| services/data/configs/launchagents/com.botquant.data_scheduler.plist | 新建 | JBT 版 LaunchAgent 模板，接管 data_scheduler 守护 |
| services/data/scripts/install_data_scheduler_launchagent.sh | 新建 | 在 Mini 上安装 / reload LaunchAgent 的脚本 |

---

## 验收标准

1. 仓内存在可复用的 JBT 版 `com.botquant.data_scheduler.plist` 模板，不再依赖 legacy `J_BotQuant` 配置。
2. 安装脚本可把模板渲染到 `~/Library/LaunchAgents/com.botquant.data_scheduler.plist`，并执行 unload/load 或 bootstrap/kickstart。
3. Mini 部署后，`launchctl list | grep com.botquant.data_scheduler` 可见该服务。
4. 在 Mini 上执行一次 `kill -9` 后，`data_scheduler` 能被 LaunchAgent 自动拉起恢复。

---

## 执行结果

1. 已新增 JBT 版 `com.botquant.data_scheduler.plist` 模板，保持与 `ops/restart-collector` 的现有 label 映射兼容。
2. 已新增安装脚本，负责渲染 plist、清理裸进程、解除 disabled 状态并在 Mini 上完成 LaunchAgent 接管。
3. Mini 运行态验证通过：`data_scheduler` 已切换为 LaunchAgent 守护，`kill -9` 后由 launchd 自动恢复，并最终收敛为单实例。
4. 锁回提交：`1ab7e28`。

---

【签名】Atlas
【时间】2026-04-11 01:30
【设备】MacBook