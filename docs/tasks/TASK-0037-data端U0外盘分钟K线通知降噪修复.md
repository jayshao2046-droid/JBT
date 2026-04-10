# TASK-0037 data端 U0 — 外盘分钟K线通知降噪修复

## 基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0037 |
| 任务类型 | U0 事后审计（单服务热修） |
| 服务 | services/data |
| 优先级 | P1（通知垃圾影响运维可观测性） |
| 触发方式 | Jay.S 直修指令 |
| 触发时间 | 2026-04-10 |
| 执行 Agent | Atlas (U0) |
| Git 提交 | `ef9d90c` |

---

## 问题描述

每 5 分钟外盘分钟K线采集 Job 执行一次，每次发送两条飞书通知卡片：
- "外盘分钟K线(yfinance) 启动" (turquoise 通知卡)
- "外盘分钟K线(yfinance) 0 条 \| 0 产出" (完成卡 with 0 bars)

高峰时段（亚洲盘，美股未开盘）每小时触发 12 次 × 2 = 24 条飞书通知，严重干扰运维告警信噪比。

---

## 根因分析

| 编号 | 根因 | 说明 |
|------|------|------|
| R1 | `_safe_run` 无条件发送"启动"卡 | `data_scheduler.py` 中 `_safe_run` 对所有 collector 都发送 start 通知 |
| R2 | `record_collection_result` 无条件发送"0产出"卡 | 每次 pipeline 完成都通知，无论 0 还是有数据 |
| R3 | Yahoo Finance IP 限速 | 27 个品种每 5 分钟批量请求，Yahoo Finance 频繁返回空数据 |

---

## 修复方案

**修复文件：** `services/data/src/scheduler/data_scheduler.py`

### 变更清单

1. **`_SILENT_COLLECTORS` 添加 `"外盘分钟K线(yfinance)"`**  
   让 `_safe_run` 跳过该 collector 的启动/完成通知。

2. **新增模块级状态字典 `_overseas_minute_session`：**
   ```python
   _overseas_minute_session: dict[str, Any] = {
       "runs": 0, "zero_runs": 0, "total_bars": 0,
       "consecutive_zeros": 0, "alerted": False,
   }
   ```

3. **`job_overseas_minute_yf()` 重写：**
   - 直接调用 `run_overseas_minute_pipeline()`，不经过 `_safe_run`
   - 更新 session 状态（runs、zero_runs、total_bars、consecutive_zeros）
   - 仅在 `consecutive_zeros >= 3`（约 15 分钟）且 `alerted == False` 时发送 P2 告警
   - 数据恢复后自动重置 `consecutive_zeros` 与 `alerted`

4. **新增 `job_overseas_minute_close_summary()`：**
   - 在 05:05 UTC（美股收盘后）触发
   - 发送"外盘分钟K线收盘摘要"卡，包含：完成率%、成功次数/总次数、累计 bars、零产出次数
   - 重置 `_overseas_minute_session` 状态

5. **注册新 CronTrigger：**
   ```python
   scheduler.add_job(job_overseas_minute_close_summary,
                     CronTrigger(hour=5, minute=5), ...)
   ```

---

## 验证结果

| 验证项 | 结果 |
|--------|------|
| Mini 重启调度器 | PID 83065，无报错 |
| `overseas_minute_yf` 注册 | ✅ `[interval 0:05:00]` 日志确认 |
| `外盘分钟K线收盘摘要` 注册 | ✅ `[cron hour=5 minute=5]` 日志确认 |
| 每 5 分钟无垃圾通知 | ✅ 运行静默，不再发"启动"/"0产出"卡 |
| 告警逻辑 | 待美股下一个交易日验证，设计逻辑已确认 |

---

## 修复边界

| 字段 | 内容 |
|------|------|
| 本次修改文件 | `services/data/src/scheduler/data_scheduler.py`（1 文件） |
| 修改行数 | +131 行 |
| 涉及服务 | services/data 单服务 |
| 是否跨服务 | 否 |
| 是否触及 P0 区域 | 否 |
| 是否触及 shared/contracts | 否 |

---

## 关联任务

- 上游：TASK-0036（外盘分钟K线 0 产出修复，提交 `300c77d`）
- 同属系统：外盘分钟K线采集子系统

---

## 状态

- [x] 直修完成
- [x] Mini 验证通过（PID 83065 运行中）
- [x] Git 提交 `ef9d90c` 推送 origin/main
- [x] 事后审计账本补齐（本文件）
