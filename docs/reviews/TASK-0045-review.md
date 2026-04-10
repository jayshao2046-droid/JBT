# TASK-0045 预审记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0045 |
| 任务标题 | Mini macOS 容器自愈守护基线 |
| 审核人 | 项目架构师（Atlas 代记录） |
| 审核日期 | 2026-04-11 |
| 审核结果 | ✅ 预审通过 |

---

## 预审检查清单

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 问题归属明确 | ✅ | 属于 Mini 宿主机部署治理，不是单服务业务代码问题 |
| 2 | 是否跨服务 / P0 | ✅ | 至少涉及 `docker-compose.mac.override.yml`，并条件性触及 `docker-compose.dev.yml` |
| 3 | 运行态依据充分 | ✅ | DR3 已在 `botquant-data` 与 `JBT-SIM-TRADING-WEB-3002` 两容器上复现实锤 |
| 4 | 最小修复路径明确 | ✅ | 优先宿主机 LaunchAgent 守护 allowlist 容器 |
| 5 | 白名单最小必要 | ✅ | 首批只冻结 override + 守护模板 + 安装脚本；base compose 条件性纳入 |
| 6 | 验收标准可复演 | ✅ | kill -9、自恢复、60s 内响应、无误伤 |

---

## 预审意见

1. 不按 data / sim-trading 双服务拆单，先作为单一部署治理任务处理，避免回滚单元碎裂。
2. 主修复路径优先采用 Mini 外部 LaunchAgent 守护 allowlist 容器；不建议把容器内 supervisor、while-true wrapper 或全项目 `docker compose up` 作为首选方案。
3. `docker-compose.dev.yml` 属于 P0 文件，只有在 `docker-compose.mac.override.yml` 无法覆盖需求时才允许条件性纳入。
4. A0 必须先冻结 allowlist 容器清单，避免把 legacy sidecar 或未稳定服务一并纳入自动拉起。

---

## 白名单冻结

### A0 批次（治理账本）

```
docs/tasks/TASK-0045-Mini-macOS-容器自愈守护基线.md
docs/reviews/TASK-0045-review.md
docs/locks/TASK-0045-lock.md
docs/handoffs/TASK-0045-架构预审交接单.md
docs/locks/TASK-0039-lock.md
docs/handoffs/TASK-0039-灾备演练执行手册.md
```

### A1 批次（已完成）

```
governance/launchagents/com.botquant.container_watchdog.plist
governance/scripts/install_container_watchdog.sh
```

> compose 文件经架构师裁定移出首批，仅宿主机 watchdog 2 文件即可独立闭环。

---

## 终审结果

| 项目 | 结果 |
|------|------|
| plist 模板 XML 校验 | ✅ plutil lint 通过 |
| install script bash 语法 | ✅ bash -n 通过 |
| Mini 部署 | ✅ LaunchAgent 已加载，runs=4 |
| botquant-data SIGKILL 自愈 | ✅ 19~46s 内恢复 |
| JBT-SIM-TRADING-WEB SIGKILL 自愈 | ✅ 42s 内恢复 |
| 非 allowlist 容器无误伤 | ✅ 确认 |
| cooldown 防重启风暴 | ✅ 120s 锁生效 |

终审结论：**✅ 通过**，TASK-0039 ISSUE-DR3-001 回写 PASS。

---

【签名】Atlas（代项目架构师记录）
【时间】2026-04-11 03:42
【设备】MacBook