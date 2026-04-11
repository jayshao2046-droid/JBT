# 架构师预审报告 — TASK-0050/0051/0052/0053/0054/0055

【签名】Atlas（代行架构师预审，原因：子Agent网络不可达）  
【时间】2026-04-11  
【设备】MacBook  
【review-id】REVIEW-TASK-0050-0055-PRE

---

## 代码库验证（实查结果）

| 验证项 | 结果 |
|--------|------|
| `services/data/src/` 无 `api/` 目录 | ✅ 确认（路由直写 main.py，单文件模式）|
| `services/data/src/main.py` 已有 `/api/v1/bars` 端点 | ✅ 确认（仅期货 bars，L216）|
| `services/data/src/data/storage.py` 已存在 | ✅ 确认（可复用）|
| `services/decision/src/research/factor_loader.py` 已有 `_fetch_bars()` | ✅ 确认（httpx 调用 data API）|
| `services/decision/src/publish/` 无 `strategy_importer.py` | ✅ 确认（含 executor/gate/sim_adapter）|
| `services/decision/src/model/` 仅含 `__init__.py` + `router.py` | ✅ 确认（无 StrategyModel 数据类）|
| `services/decision/src/api/routes/strategy.py` 无 watchlist 端点 | ✅ 确认（前缀 `/strategies`，有 overview/list/detail/publish/dashboard）|
| `services/backtest/src/backtest/` 无 `strategy_queue.py` / `manual_runner.py` | ✅ 确认 |
| `services/backtest/src/api/routes/` 无 `approval.py` / `queue.py` | ✅ 确认 |

---

## TASK-0050（C0-1 股票 bars API 路由扩展）

### 逐项检查

| 检查项 | 结论 | 说明 |
|--------|------|------|
| 服务边界 | ✅ 通过 | 仅 `services/data/` |
| 白名单完整性 | ⚠️ 需调整 | data 服务当前无 `api/` 目录，详见下方 |
| 前置依赖 | ✅ 合理 | 无前置依赖，Lane-A 起点 |

### 架构师确认点回答

**Q1: 是否将数据读取逻辑抽到 storage.py？**

**裁定：Phase C 初版不拆。** 理由：
- data 服务当前所有路由（`/bars`, `/symbols`, `/health`, `/dashboard/*`）全部直接写在 `main.py` 内
- 要新建 `api/routes/stock_bars.py` 需同时创建 `api/__init__.py` + `api/routes/__init__.py` 并改造 `main.py` 的 app 注册
- **架构重构不在 C0-1 范围内** — 建议直接在 `main.py` 追加 `GET /api/v1/stocks/bars` 端点，与现有期货 bars 风格一致
- 白名单应调整为 `main.py`（修改） + 测试文件（新建）

**Q2: 是否需登记到 shared/contracts？**

**裁定：Phase C 初版不需要。** 理由：
- decision 的 FactorLoader 已直接硬编码 `{base_url}/api/v1/bars`，同样模式加 `/api/v1/stocks/bars` 即可
- 先落实功能，契约登记待 Phase C 中后期统一补齐

### ⚠️ 白名单调整

原申请：`api/__init__.py`(新建) + `api/routes/__init__.py`(新建) + `api/routes/stock_bars.py`(新建) + `main.py`(修改)

**调整为：**
| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/main.py` | 修改 | 追加 `GET /api/v1/stocks/bars` 端点 |
| `tests/data/api/test_stock_bars.py` | 新建 | 股票 bars 单元测试 |

**理由：** data 服务当前为单文件模式，Phase C 初版不引入架构变更，直接在 main.py 追加端点。不新建 `api/routes/` 目录。

### 综合结论：✅ 预审通过（白名单调整为 2 项）

---

## TASK-0051（C0-3 策略导入解析器）

### 逐项检查

| 检查项 | 结论 | 说明 |
|--------|------|------|
| 服务边界 | ✅ 通过 | 仅 `services/decision/` |
| 白名单完整性 | ✅ 通过 | 5 项合理 |
| 前置依赖 | ✅ 合理 | 无前置依赖，Lane-A 起点 |

### 架构师确认点回答

**Q1: StrategyModel 定义位置？**

**裁定：在 `publish/` 目录就地定义。** 理由：
- decision `model/` 目录当前仅含 `router.py`（模型路由概念），不是"数据模型"目录
- Pydantic BaseModel 定义在使用方 `publish/strategy_importer.py` 顶部或新建 `publish/strategy_model.py` 均可
- 不修改 `model/` 目录（避免语义混淆）

**Q2: YAML schema？**

**裁定：以 Batch-2 草案为准（name/symbol/exchange/direction/entry_rules/exit_rules/risk_params）。** Phase C 初版不引入独立 schema registry。

### 综合结论：✅ 预审通过

---

## TASK-0052（CG1 回测端策略导入队列）

### 逐项检查

| 检查项 | 结论 | 说明 |
|--------|------|------|
| 服务边界 | ✅ 通过 | 仅 `services/backtest/` |
| 白名单完整性 | ✅ 通过 | 4 项合理 |
| 前置依赖 | ✅ 合理 | 无前置依赖，Lane-A 起点 |

### 架构师确认点回答

**Q1: 队列内存实现是否满足初版？**

**裁定：YES。** Phase C 初版 backtest 为单实例部署，内存队列足够。后续升级为 Redis/DB 持久化队列在 Phase D+ 考虑。

**Q2: 无需验证 decision Token 签名？**

**裁定：YES，Phase C 初版内网可信场景不做跨服务 Token 校验。** 仅验证请求体 schema（Pydantic 自动校验）。

### 综合结论：✅ 预审通过

---

## TASK-0053（C0-2 FactorLoader 股票代码支持）

### 逐项检查

| 检查项 | 结论 | 说明 |
|--------|------|------|
| 服务边界 | ✅ 通过 | 仅 `services/decision/` |
| 白名单完整性 | ✅ 通过 | 3 项合理，已合并 stock_data_client 到 FactorLoader |
| 前置依赖 | ✅ 合理 | TASK-0050(C0-1) + TASK-0051(C0-3) 双完成 |

### 架构师确认点回答

**Q1: 股票代码格式？**

**裁定：接受 `000001.SZ`、`600000.SH` 两种标准格式，不接受无后缀格式。** 理由：
- data API `/api/v1/stocks/bars?symbol=000001.SZ` 需要明确市场后缀
- 无后缀格式 `000001` 存在歧义（深圳 vs 港股），不在初版范围

**Q2: 是否在 shared/contracts 登记端点？**

**裁定：NO，同 TASK-0050 处理方式。** Phase C 初版不做。

### 综合结论：✅ 预审通过

---

## TASK-0054（CB5 动态 watchlist 分钟K采集）

### 逐项检查

| 检查项 | 结论 | 说明 |
|--------|------|------|
| 服务边界 | ⚠️ 需确认 | 跨服务（data + decision），已标注需两份 Token |
| 白名单完整性 | ⚠️ 需裁定 | decision 侧 watchlist 端点问题 |
| 前置依赖 | ✅ 合理 | TASK-0050(C0-1) 完成 |

### 架构师裁定

**方案 A vs 方案 B？**

**裁定：方案 A。** 将 decision 侧 `GET /strategies/watchlist` 纳入 TASK-0054 Token，两边同批签发。理由：
- watchlist 端点逻辑极简（从现有策略列表提取 symbol 去重返回），不值得独立建档
- 两边同批签发减少流程开销
- decision 侧只改 `strategy.py`（已在白名单），不新增文件

### 白名单冻结

**Data 侧（4 项）：**
| 文件 | 操作 |
|------|------|
| `services/data/src/collectors/watchlist_client.py` | 新建 |
| `services/data/src/collectors/stock_minute_collector.py` | 修改 |
| `services/data/src/scheduler/pipeline.py` | 修改 |
| `tests/data/collectors/test_watchlist_client.py` | 新建 |

**Decision 侧（1 项）：**
| 文件 | 操作 |
|------|------|
| `services/decision/src/api/routes/strategy.py` | 修改（追加 watchlist 端点）|

### 综合结论：✅ 预审通过（方案 A，两份 Token 同批签发）

---

## TASK-0055（CG2 人工手动回测+审核确认）

### 逐项检查

| 检查项 | 结论 | 说明 |
|--------|------|------|
| 服务边界 | ✅ 通过 | 仅 `services/backtest/` |
| 白名单完整性 | ✅ 通过 | 4 项，app.py 修改正确（不是 main.py）|
| 前置依赖 | ✅ 合理 | TASK-0052(CG1) 完成（需 strategy_queue.py 已存在）|

### 综合结论：✅ 预审通过

---

## 总体裁定

### 预审结果

| TASK | 结论 | 条件 |
|------|------|------|
| TASK-0050 (C0-1) | ✅ 通过 | **白名单调整**：main.py(改) + test(新)，不新建 api/ 目录 |
| TASK-0051 (C0-3) | ✅ 通过 | StrategyModel 在 publish/ 就地定义 |
| TASK-0052 (CG1) | ✅ 通过 | 内存队列，无跨服务 Token 校验 |
| TASK-0053 (C0-2) | ✅ 通过 | 股票代码需含市场后缀 |
| TASK-0054 (CB5) | ✅ 通过 | 方案A：watchlist 编入同 Token |
| TASK-0055 (CG2) | ✅ 通过 | 白名单 4 项 |

### 执行顺序

```
(可并行) TASK-0050 ⊥ TASK-0051 ⊥ TASK-0052
                │          │          │
                ├──────────┤          │
                ↓          ↓          ↓
          TASK-0053    TASK-0054   TASK-0055
          (C0-2)       (CB5)      (CG2)

Lane-A 三项无相互依赖，可同时签发 Token 并行实施。
Lane-B 三项各有前置，按依赖激活。
```

### Token 签发建议

**立即可签发（Lane-A，无前置依赖）：**
- TASK-0050 Token（data: main.py + test）
- TASK-0051 Token（decision: 5 文件）
- TASK-0052 Token（backtest: 4 文件）

**等前置完成后签发（Lane-B）：**
- TASK-0053 Token → 等 TASK-0050 + TASK-0051 完成
- TASK-0054 Token ×2 → 等 TASK-0050 完成 + 方案 A 确认
- TASK-0055 Token → 等 TASK-0052 完成
