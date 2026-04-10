# TASK-0027 锁控记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0027 |
| 任务标题 | data 端全量采集体系迁移到 JBT |
| 锁控管理人 | 项目架构师 |
| 创建日期 | 2026-04-08 |

---

## 锁控文件清单

### A0 批次（治理建档）— 协同账本区，无需 Token

| 文件 | 操作 | 状态 | 写入者 |
|------|------|------|--------|
| docs/tasks/TASK-0027-data端全量采集体系迁移.md | 新建 | ✅ 已完成 | 项目架构师 |
| docs/reviews/TASK-0027-review.md | 新建 | ✅ 已完成 | 项目架构师 |
| docs/locks/TASK-0027-lock.md | 新建 | ✅ 已完成 | 项目架构师 |
| docs/handoffs/TASK-0027-架构预审交接单.md | 新建 | ✅ 已完成 | 项目架构师 |

### A1 批次（采集器 + 公共依赖）— ✅ locked

| 文件 | 操作 | 状态 | 保护级别 |
|------|------|------|----------|
| services/data/src/collectors/** (21文件) | 新建 | ✅ locked (`tok-c4aa180a`) | P1 |
| services/data/src/utils/** (6文件) | 新建 | ✅ locked (`tok-c4aa180a`) | P1 |
| services/data/src/models/** (1文件) | 新建 | ✅ locked (`tok-c4aa180a`) | P1 |

### A2 批次（调度器）— ✅ locked

| 文件 | 操作 | 状态 | 保护级别 |
|------|------|------|----------|
| services/data/src/scheduler/** (3文件) | 新建 | ✅ locked (`tok-c4aa180a`) | P1 |

### A3 批次（健康 + 心跳 + 重连）— ✅ locked

| 文件 | 操作 | 状态 | 保护级别 |
|------|------|------|----------|
| services/data/src/health/** (4文件) | 新建 | ✅ locked (`tok-c4aa180a`) | P1 |

### A4 批次（备份 + 清理 + NAS）— ✅ locked

| 文件 | 操作 | 状态 | 保护级别 |
|------|------|------|----------|
| services/data/src/ops/** (4文件) | 新建 | ✅ locked (`tok-c4aa180a`) | P1 |

### A5 批次（联调）— 已完成并锁回

| 文件 | 操作 | 状态 | 保护级别 |
|------|------|------|----------|
| services/data/tests/test_collectors.py | 修改 | 🔒 locked (`tok-4f75a1c4`) | P1 |
| services/data/tests/test_scheduler.py | 修改 | 🔒 locked (`tok-4f75a1c4`) | P1 |
| services/data/tests/test_main.py | 修改 | 🔒 locked (`tok-4f75a1c4`) | P1 |
| services/data/tests/test_notify.py | 修改 | 🔒 locked (`tok-4f75a1c4`) | P1 |

### A6 批次（通知系统重做）— 需 Jay.S 签单 + Token

| 文件 | 操作 | 状态 | 保护级别 |
|------|------|------|----------|
| services/data/src/notify/** | 新建 | 🔒 待解锁 | P0 |

### A7 批次（Mini Docker 接入）— 需 Jay.S Token

| 文件 | 操作 | 状态 | 保护级别 |
|------|------|------|----------|
| docker-compose.dev.yml | 修改 | 🔒 待解锁 | P0 |
| services/data/.env.example | 修改 | 🔒 待解锁 | P0 |
| services/data/Dockerfile | 新建/修改 | 🔒 待解锁 | P0 |

---

## 锁控日志

| 时间 | 操作 | 批次 | 说明 |
|------|------|------|------|
| 2026-04-08 | 建档 | A0 | 创建锁控记录，A0 文件全部完成 |
| 2026-04-10 | issue | A5 | Jay.S 签发 `tok-4f75a1c4`，4 文件，3-day TTL |
| 2026-04-10 | lockback | A5 | 124 passed 3 skipped，架构师终审通过，执行锁回 |
| 2026-04-10 | issue | A1-A4 | Jay.S 签发 `tok-c4aa180a`，39文件，3-day TTL，补办lockback |
| 2026-04-10 | validate | A1-A4 | Token 校验通过，6文件抽样验证 |
| 2026-04-10 | lockback | A1-A4 | 补办lockback approved，39文件全部locked |

---

## 结论

TASK-0027 批次 A0~A5 全部 locked 闭环。A6（通知）已由 TASK-0028 覆盖。A7（Docker P0文件）待后续处理。

---

【签名】Atlas
【时间】2026-04-10
【设备】MacBook
