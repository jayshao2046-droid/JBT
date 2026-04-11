# Lane-A Token 签发记录（TASK-0050 / TASK-0051 / TASK-0052）

【签名】Atlas  
【时间】2026-04-12  
【设备】MacBook  
【预审报告】docs/reviews/REVIEW-TASK-0050-0055-预审.md  

---

## 签发总览

| # | Token ID | 任务 | Agent | 文件数 | 状态 |
|---|----------|------|-------|--------|------|
| 1 | `tok-b7358d64` | TASK-0050 | 数据 | 2 | ✅ 已签发 |
| 2 | `tok-2e393387` | TASK-0051 | 决策 | 5 | ✅ 已签发 |
| 3 | `tok-5d4f2cca` | TASK-0052 | 回测 | 4 | ✅ 已签发 |

---

## Token-1: TASK-0050 — C0-1 股票 bars API 路由扩展

| 字段 | 值 |
|------|-----|
| token_id | `tok-b7358d64-38bd-4ea4-85b7-9be69f4635f6` |
| task_id | TASK-0050 |
| agent | 数据 |
| action | C0-1 股票 bars API 路由扩展 |
| review_id | REVIEW-TASK-0050-0055-PRE |
| notes | Phase C Lane-A 首批，白名单调整为 main.py+test（不新建 api/ 目录） |

**白名单（2 文件）：**
1. `services/data/src/main.py`（修改）
2. `tests/data/api/test_stock_bars.py`（新建）

---

## Token-2: TASK-0051 — C0-2 策略文件导入器

| 字段 | 值 |
|------|-----|
| token_id | `tok-2e393387-f5a8-42bc-8ded-98be945f9e43` |
| task_id | TASK-0051 |
| agent | 决策 |
| action | C0-2 策略文件导入器 |
| review_id | REVIEW-TASK-0050-0055-PRE |
| notes | Phase C Lane-A，StrategyModel 在 publish/ 而非 model/ |

**白名单（5 文件）：**
1. `services/decision/src/publish/strategy_importer.py`（新建）
2. `services/decision/src/publish/yaml_importer.py`（新建）
3. `services/decision/src/api/routes/strategy_import.py`（新建）
4. `services/decision/src/api/app.py`（修改）
5. `tests/publish/test_strategy_importer.py`（新建）

---

## Token-3: TASK-0052 — C0-3 回测策略队列

| 字段 | 值 |
|------|-----|
| token_id | `tok-5d4f2cca-0a67-492c-bd5f-74f025ad329d` |
| task_id | TASK-0052 |
| agent | 回测 |
| action | C0-3 回测策略队列 |
| review_id | REVIEW-TASK-0050-0055-PRE |
| notes | Phase C Lane-A，内存队列方案，不需跨服务 Token |

**白名单（4 文件）：**
1. `services/backtest/src/backtest/strategy_queue.py`（新建）
2. `services/backtest/src/api/routes/queue.py`（新建）
3. `services/backtest/src/api/app.py`（修改）
4. `tests/api/test_strategy_import.py`（新建）

---

## 备注

- Lane-A 三项任务无前后依赖，可同时签发、并行实施
- Lane-B（TASK-0053/0054/0055）须等 Lane-A 完成后才能签发
- TASK-0051/0052 已签发（2026-04-12 Jay.S 终端输入密码完成）
