# TASK-0045 Mini macOS 容器自愈守护基线

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0045 |
| 任务标题 | Mini macOS 容器自愈守护基线 |
| 服务归属 | 部署治理 / Mini 宿主机 |
| 执行 Agent | 项目架构师 / Atlas |
| 优先级 | P1 |
| 来源 | TASK-0039 / ISSUE-DR3-001 |
| 状态 | 建档完成，待预审执行 |

---

## 背景

1. `TASK-0039` DR3 演练确认：Mini(macOS, Docker 29.2.1) 上对 `botquant-data` 与 `JBT-SIM-TRADING-WEB-3002` 执行 `docker kill --signal=KILL` 后，容器均停留在 `Exited(137)`，`restart: unless-stopped` 未自动恢复。
2. 当前仓内 `docker-compose.dev.yml` 仅 `jbt-data` 声明了 `restart: unless-stopped`，而 DR3 失败证明在 Mini 宿主机上不能把 compose restart policy 当作充分自愈保证。
3. `TASK-0043` 已验证 Mini 上 LaunchAgent 路径可用，因此 DR3 的最小修复方向优先考虑“宿主机外部守护 allowlist 容器”，而不是扩散到服务代码或容器内 supervisor。

---

## 白名单冻结

### A0 批次（治理账本，无需 Token）

| 文件 | 操作 | 说明 |
|------|------|------|
| docs/tasks/TASK-0045-Mini-macOS-容器自愈守护基线.md | 新建 | 任务建档 |
| docs/reviews/TASK-0045-review.md | 新建 | 预审结论 |
| docs/locks/TASK-0045-lock.md | 新建 | 锁控记录 |
| docs/handoffs/TASK-0045-架构预审交接单.md | 新建 | 派发与交接 |
| docs/locks/TASK-0039-lock.md | 更新 | 将 ISSUE-DR3-001 挂接到 TASK-0045 |
| docs/handoffs/TASK-0039-灾备演练执行手册.md | 更新 | DR3 修复任务回指 |

### A1 批次（待预审冻结，P0/P1 混合）

| 文件 | 操作 | 说明 |
|------|------|------|
| docker-compose.mac.override.yml | 更新 | Mini/macOS 平台差异补充口径 |
| governance/launchagents/com.botquant.container_watchdog.plist | 新建 | Mini 用户级容器守护模板 |
| governance/scripts/install_container_watchdog.sh | 新建 | 安装 / reload 容器守护脚本 |
| docker-compose.dev.yml | 条件性更新 | 仅在架构终审确认必须时纳入，不默认解锁 |

---

## 预期修复口径

1. 宿主机守护只监控明确 allowlist 容器，不执行全项目 `docker compose up`。
2. `docker-compose.mac.override.yml` 仅承载 macOS 平台差异，不把 Mini 专属 workaround 直接扩散到通用编排。
3. `docker-compose.dev.yml` 只有在确认属于跨主机统一基线、且最小变更无法仅靠 override 覆盖时才允许纳入。
4. 不修改任一 `services/**` 业务代码，不引入容器内 supervisor / while-true wrapper。

---

## 验收标准

1. A0 先冻结 Mini allowlist 容器清单，并明确是否纳入 `botquant-data`。
2. 对纳入 allowlist 的每个容器执行 `docker kill --signal=KILL` 后，60 秒内必须自动恢复到可响应状态。
3. LaunchAgent / watchdog 在 Mini 用户态可见，且同一故障只触发一次恢复动作，不产生重复实例或重启风暴。
4. 未纳入 allowlist 的容器不得被误拉起或误重启。
5. `TASK-0039` 的 DR3 复演结果可回写为通过。

---

【签名】Atlas
【时间】2026-04-11
【设备】MacBook