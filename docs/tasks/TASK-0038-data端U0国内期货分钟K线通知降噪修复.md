# TASK-0038 data端 U0 — 国内期货分钟K线通知降噪修复

## 基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0038 |
| 任务类型 | U0 事后审计（单服务热修） |
| 服务 | services/data |
| 优先级 | P1（通知垃圾影响运维可观测性） |
| 触发方式 | Jay.S 直修指令 |
| 触发时间 | 2026-04-10 |
| 执行 Agent | Atlas (U0) |
| Git 提交 | `e3a2fd6` |

---

## 问题描述

国内期货分钟K线采集 Job 每 2 分钟触发一次，`_safe_run` 每次无条件发送：
- "分钟内盘K线 启动"（turquoise 通知卡）
- "分钟内盘K线 完成 / 0产出"（完成卡）

交易时段（日盘 4.5h + 夜盘最多 5.5h）每天约 **140 条**飞书通知，严重影响运维告警信噪比。

---

## 根因分析

| 编号 | 根因 | 说明 |
|------|------|------|
| R1 | `_safe_run` 无条件发启动卡 | `"分钟内盘K线"` 不在 `_SILENT_COLLECTORS` 中 |
| R2 | `record_collection_result` 无条件发完成卡 | 每轮 pipeline 结束均推通知，无论有无数据 |
| R3 | 无 session 状态跟踪 | 无法区分单次抖动与持续异常 |

---

## 修复方案

**修复文件：** `services/data/src/scheduler/data_scheduler.py`（1 文件，+138 行，-5 行）

### 变更清单

1. **`_SILENT_COLLECTORS` 加入 `"分钟内盘K线"`**  
   让 `_safe_run` 跳过启动/完成通知。

2. **新增模块级状态字典 `_domestic_minute_session`：**
   ```python
   _domestic_minute_session: dict[str, Any] = {
       "runs": 0, "zero_runs": 0, "total_bars": 0,
       "consecutive_zeros": 0, "alerted": False,
   }
   ```

3. **`job_minute_kline()` 重写为 session 模式：**
   - 直接调用 `run_minute_pipeline()`，不经过 `_safe_run`
   - 更新 session 状态
   - 连续 `consecutive_zeros >= 3`（约 6 分钟）且 `alerted == False` → 发 P2 告警
   - 有数据后自动重置 `consecutive_zeros` 与 `alerted`

4. **新增内部函数 `_domestic_minute_close_summary(session_name)`：**
   - 计算完整度（有数据轮次/总轮次），按百分比选 🟢/🟡/🔴 图标
   - 发"收盘摘要"NOTIFY 卡，包含完整度%、有数据轮次、累计 bars、0产出轮次
   - 重置 `_domestic_minute_session` 状态

5. **新增 `job_domestic_minute_day_close()`（15:05）和 `job_domestic_minute_night_close()`（02:35）**

6. **注册两个 CronTrigger：**
   ```
   CronTrigger(hour=15, minute=5,  day_of_week="mon-fri")   # 日盘收盘摘要
   CronTrigger(hour=2,  minute=35, day_of_week="tue-sat")   # 夜盘收盘摘要
   ```

---

## 验证结果

| 验证项 | 结果 |
|--------|------|
| Mini 重启调度器 | PID 84318，无报错 |
| `分钟内盘K线` 注册 | ✅ `[interval 0:02:00]` 日志确认 |
| `国内期货日盘收盘摘要` 注册 | ✅ `[cron day_of_week='mon-fri', hour='15', minute='5']` |
| `国内期货夜盘收盘摘要` 注册 | ✅ `[cron day_of_week='tue-sat', hour='2', minute='35']` |
| 每 2 分钟无垃圾通知 | ✅ 运行静默 |
| 告警/摘要逻辑 | 待下一日盘完整验证（设计逻辑已确认） |

---

## 修复边界

| 字段 | 内容 |
|------|------|
| 本次修改文件 | `services/data/src/scheduler/data_scheduler.py`（1 文件） |
| 净增行数 | +138 行 |
| 涉及服务 | services/data 单服务 |
| 是否跨服务 | 否 |
| 是否触及 P0 区域 | 否 |
| 是否触及 shared/contracts | 否 |

---

## 关联任务

- 同类先例：TASK-0037（外盘分钟K线通知降噪，提交 `ef9d90c`）
- 同属系统：data 端调度器通知治理

---

## 效果对比

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 每日飞书通知数（日盘+夜盘） | ~140 条 | **2 条**（日盘摘要 + 夜盘摘要） |
| 异常时 | 无 P 级告警 | 连续 6 分钟无数据发 P2 |
| session 感知 | 无 | 完整度%、累计 bars、0产出次数 |

---

## 状态

- [x] 直修完成
- [x] Mini 验证通过（PID 84318 运行中）
- [x] Git 提交 `e3a2fd6` 推送 origin/main
- [x] 事后审计账本补齐（本文件）
