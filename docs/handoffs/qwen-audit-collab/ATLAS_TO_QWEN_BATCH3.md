# Atlas → Qwen Batch-3 派发单

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  

---

## ⏳ 本批次激活条件

**必须等待以下三个任务全部完成并经 Jay.S 确认后，才能开始本批次：**

| 前置任务 | 说明 |
|----------|------|
| TASK-0050 C0-1 实施完成 | C0-1 stock_bars API 上线（解锁 CB5 + C0-2）|
| TASK-0051 C0-3 实施完成 | C0-3 策略导入解析器上线（解锁 C0-2）|
| TASK-0052 CG1 实施完成 | CG1 回测导入队列上线（解锁 CG2）|

---

## ⚠️ 强制质量要求（与 Batch-2 相同，继续执行）

1. **零瑕疵原则**：每次提交前必须自查，目标 100 分，低于 80 分 Atlas 暂停流程。
2. **锚点声明义务**：每份规格书必须有独立 §锚点声明，分类：已存在 / 新建 / planned-placeholder。
3. **绝对禁止**：将 planned-placeholder 写为已存在锚点。
4. **app.py 意识**：backtest 和 decision 两个服务的路由注册都在 `api/app.py`，**不是 main.py**，白名单必须精确填写。
5. **依赖闭环义务**：提交前对照 `QWEN_PHASE_C_STEP3_REPORT.md` §4 并行关系图确认。

---

## 输入材料（必须在激活后完整阅读）

| 材料 | 路径 |
|------|------|
| Atlas–Qwen SOP | `docs/handoffs/qwen-audit-collab/ATLAS_QWEN_SOP.md` |
| 全量部署编排 | `docs/handoffs/qwen-audit-collab/QWEN_PHASE_C_STEP3_REPORT.md` |
| Batch-2 接口约定 | `docs/handoffs/qwen-audit-collab/QWEN_INTERFACE_DRAFT_BATCH2.md` |
| C0-1 规格书（已 Atlas 补漏）| `docs/handoffs/qwen-audit-collab/QWEN_SPEC_C0-1_STOCK_BARS_API.md` |
| C0-3 规格书（已 Atlas 补漏）| `docs/handoffs/qwen-audit-collab/QWEN_SPEC_C0-3_STRATEGY_IMPORTER.md` |
| CG1 规格书（已 Atlas 补漏）| `docs/handoffs/qwen-audit-collab/QWEN_SPEC_CG1_STRATEGY_QUEUE.md` |
| decision api/app.py | `services/decision/src/api/app.py` |
| backtest api/app.py | `services/backtest/src/api/app.py` |
| data collectors 目录 | `services/data/src/collectors/` |
| data scheduler | `services/data/src/scheduler/pipeline.py` |
| decision research 目录 | `services/decision/src/research/` |

---

## 子任务清单（共 4 项）

---

### Task B3-1：C0-2 实施规格书

**输出文件**：`QWEN_SPEC_C0-2_FACTOR_LOADER_STOCK.md`

#### §2 锚点声明（参考格式）
- 已存在：`services/decision/src/research/factor_loader.py`（核查实际路径是否存在）
- 新建：`services/decision/src/research/stock_data_client.py`
- 修改：`services/decision/src/research/factor_loader.py`（扩展股票 symbol 支持）

#### §3 接口规范
- `FactorLoader.load_stock_bars(symbol, start, end, timeframe_minutes=1)` 方法签名
- `StockDataClient.get_bars(...)` HTTP 客户端方法签名（调用 `GET /api/v1/stocks/bars`）
- 返回数据类型定义（pandas DataFrame + 必需字段）

#### §4 HTTP 客户端设计
- 重试机制（最多 3 次，指数退避）
- 超时设置（connect 3s，read 30s）
- 环境变量：`JBT_DATA_API_URL`（来自 PORT_REGISTRY.md，data 服务端口 8105）

#### §5 错误处理清单
- data 服务 404 → FactorLoader 抛出具名异常
- data 服务超时 → 抛出 `DataServiceTimeoutError`
- data 服务返回非预期格式 → 抛出 `DataParseError`

#### §6 测试用例（最少 8 条）
- 必须包含：mock HTTP 请求、超时重试、格式解析、期货回归（原有 `load_futures_bars` 不受影响）

#### §7 依赖关系
- 前置：C0-1 + C0-3 双完成
- 解锁：CA2' / CB2'

---

### Task B3-2：CB5 实施规格书

**输出文件**：`QWEN_SPEC_CB5_WATCHLIST_COLLECTOR.md`

#### 注意
CB5 是**跨服务任务**，需要说明 watchlist 数据来源（decision 服务），但不得直接 import decision 代码，只能通过 HTTP。

#### §2 锚点声明（参考格式）
- 已存在：
  - `services/data/src/collectors/stock_minute_collector.py`（主采集器，需扩展）
  - `services/data/src/scheduler/pipeline.py`（调度，需扩展）
- 新建：
  - `services/data/src/collectors/watchlist_client.py`（HTTP 调用 decision watchlist API）
- 修改：
  - `services/data/src/collectors/stock_minute_collector.py`（动态 symbol 支持）
  - `services/data/src/scheduler/pipeline.py`（新增 watchlist 刷新调度）
  - **decision 服务 API 路由**：先读取 decision 服务现有 strategy/signal 路由，确认 watchlist 端点是否已存在；若不存在，在规格书 §2 planned-placeholder 中说明，并标注 "CB5 前置：需 decision 服务先提供 watchlist API"

#### §3 接口规范
- `GET /api/v1/strategies/watchlist`（decision 服务，需确认是否已存在）
- `WatchlistClient.fetch_watchlist()` 方法签名
- 降级策略：decision 不可达时，读取本地缓存文件（路径规范）

#### §6 测试用例（最少 8 条）
- 必须包含：mock decision API、降级到缓存、空 watchlist 边界、采集 symbol 列表验证

---

### Task B3-3：CG2 实施规格书

**输出文件**：`QWEN_SPEC_CG2_MANUAL_BACKTEST.md`

#### §2 锚点声明（参考格式）
- 已存在：
  - `services/backtest/src/backtest/runner.py`（回测执行核心，只调用不修改）
  - `services/backtest/src/backtest/strategy_queue.py`（CG1 建立，本任务消费）
  - `services/backtest/src/api/app.py`（路由注册）
- 新建：
  - `services/backtest/src/backtest/manual_runner.py`
  - `services/backtest/src/api/routes/approval.py`
- 修改：
  - `services/backtest/src/api/app.py`（注册 approval router）
  - `services/backtest/src/backtest/strategy_queue.py`（CG1 的 strategy_queue 需要扩展 running 状态）

#### §3 状态机（必须完整定义）
```
queued → running → completed / failed
                ↘ approved / rejected  (审核层，叠加在 completed 之上)
```

#### §4 human-in-the-loop 流程
- `POST /api/v1/backtest/manual/run` → 触发 manual_runner → 调用 runner.py → 返回 run_id
- `GET /api/v1/backtest/approval/{run_id}` → 获取回测结果摘要（含绩效指标）
- `POST /api/v1/backtest/approval/{run_id}/approve` → 审核通过
- `POST /api/v1/backtest/approval/{run_id}/reject` → 拒绝，附 reason 字段

#### §6 测试用例（最少 8 条）
- 必须包含：触发回测、获取结果、approve、reject、重复 approve 边界、run_id 不存在 404

---

### Task B3-4：Batch-3 端到端验收场景

**输出文件**：`QWEN_E2E_ACCEPTANCE_BATCH3.md`

内容格式与 `QWEN_E2E_ACCEPTANCE_BATCH2.md` 相同：
- §1 C0-2 验收场景（最少 5 条）
- §2 CB5 验收场景（最少 5 条）
- §3 CG2 验收场景（最少 5 条）
- §4 回归测试覆盖确认（三个服务各自的现有路由列表）

---

## 输出要求

| 输出文件 | 最低行数 |
|----------|---------|
| `QWEN_SPEC_C0-2_FACTOR_LOADER_STOCK.md` | 160 行 |
| `QWEN_SPEC_CB5_WATCHLIST_COLLECTOR.md` | 160 行 |
| `QWEN_SPEC_CG2_MANUAL_BACKTEST.md` | 180 行 |
| `QWEN_E2E_ACCEPTANCE_BATCH3.md` | 120 行 |

**所有文件均输出到** `docs/handoffs/qwen-audit-collab/`

---

## 完成后提交方式

创建 `QWEN_BATCH3_COMPLETE.md`，包含：
1. 4 个输出文件路径
2. Qwen 自评分（5 维度各打分 + 理由）
3. 自查清单（锚点声明已填 / 依赖与 Step3 图一致 / 无空表格单元格 / app.py 注册文件正确）
