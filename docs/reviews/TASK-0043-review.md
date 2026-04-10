# TASK-0043 预审记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0043 |
| 任务标题 | data_scheduler 守护切换到 LaunchAgent |
| 审核人 | 项目架构师（Atlas 代记录） |
| 审核日期 | 2026-04-11 |
| 审核结果 | ✅ 预审通过 |

---

## 预审检查清单

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 服务归属明确 | ✅ | 仅 data 单服务 |
| 2 | 不涉及跨服务 | ✅ | 仅 data 自身配置与安装脚本 |
| 3 | 不涉及共享契约/P0 文件 | ✅ | 无 `shared/contracts`、`.github`、`docker-compose.dev.yml` 修改 |
| 4 | 运行态依据充分 | ✅ | Mini 已确认现网为裸进程；历史 LaunchAgent 文件可供对照 |
| 5 | 白名单最小必要 | ✅ | 仅 1 个 plist 模板 + 1 个安装脚本 |
| 6 | 验收标准明确 | ✅ | 模板落库、Mini 安装、kill 恢复三层验证 |

---

## 预审意见

1. 保持 `com.botquant.data_scheduler` label 不变，避免破坏 `ops/restart-collector` 既有白名单映射。
2. 不扩大到其他 collector 的 LaunchAgent 整理；本任务只解决 `data_scheduler` 主进程守护缺失。
3. 不把 `data_scheduler` 再塞回 Docker；当前采用用户级 LaunchAgent 是最小可落地修复。

---

## 白名单冻结

```
services/data/configs/launchagents/com.botquant.data_scheduler.plist
services/data/scripts/install_data_scheduler_launchagent.sh
```

---

【签名】Atlas（代项目架构师记录）
【时间】2026-04-11 01:15
【设备】MacBook