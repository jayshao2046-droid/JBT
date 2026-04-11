# Atlas → Qwen Batch-5 派发单

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  

---

## ⏳ 本批次激活条件

**必须等待以下全部完成并经 Jay.S 确认后启动：**

| 前置任务 | 解锁项 |
|----------|--------|
| TASK-0051 C0-3 完成 | 解锁 CF2 |
| TASK-0056 CA2' 完成 | 解锁 CA3/CA4 |
| TASK-0057 CB2' 完成 | 解锁 CB3 |

---

## ⚠️ 强制质量要求（同 Batch-2/3/4，继续执行）

1. 零瑕疵原则，100 分目标，低于 80 分 Atlas 暂停。
2. §锚点声明 必填；已存在 / 新建 / planned-placeholder 三类严格分开。
3. 路由注册在 `api/app.py`（decision/backtest），sim-trading 路由注册在 `api/router.py`。
4. 跨服务任务必须显式标注"需独立 Token"（**本批次 CF2 单服务，无跨服务**）。
5. §4 数据流设计必须包含 sequence diagram（文字版），描述 API 层→业务层→数据层完整调用链。
6. **新增要求**：CA3/CA4 必须明确复用 CA2' 输出的 `sandbox_engine.py` 的具体方法，禁止重复实现回测逻辑。

---

## 输入材料

| 材料 | 路径 |
|------|------|
| SOP | `docs/handoffs/qwen-audit-collab/ATLAS_QWEN_SOP.md` |
| 全量编排 | `docs/handoffs/qwen-audit-collab/QWEN_PHASE_C_STEP3_REPORT.md` |
| CA2' 规格书（Atlas 审后版）| `docs/handoffs/qwen-audit-collab/QWEN_SPEC_CA2P_FUTURES_SANDBOX.md` |
| CB2' 规格书（Atlas 审后版）| `docs/handoffs/qwen-audit-collab/QWEN_SPEC_CB2P_STOCK_SANDBOX.md` |
| C0-3 规格书（Atlas 审后版）| `docs/handoffs/qwen-audit-collab/QWEN_SPEC_C0-3_STRATEGY_IMPORTER.md` |
| decision api/app.py | `services/decision/src/api/app.py` |
| decision research/ 目录 | `services/decision/src/research/`（含 session.py/trainer.py/optuna_search.py）|
| decision optuna_search.py | `services/decision/src/research/optuna_search.py` |

---

## 子任务清单（共 5 项）

---

### Task B5-1：CA3 回测报告展示与导出规格书

**输出文件**：`QWEN_SPEC_CA3_SANDBOX_REPORT.md`

**服务**：`services/decision/`  
**依赖**：CA2'（sandbox_engine.py 必须已完成，提供 `run_backtest()` 返回的 result 结构）  
**目标**：在 decision 服务内展示沙箱回测结果，并支持导出为 JSON/CSV

#### 必须回答的问题
- `sandbox_engine.py` 的 `run_backtest()` 返回什么结构？CA3 从哪里读取这个结果？
- 报告展示端点是 REST API（JSON 返回）还是 HTML 页面？**明确选择其一**（推荐：REST API 返回 JSON，看板页面用 CA5 实现）

#### §2 锚点声明
- 已存在：`research/session.py`（ResearchSession），`research/sandbox_engine.py`（CA2' 产出）
- 新建：`research/report_builder.py`（格式化 sandbox 结果为报告结构）
- 新建路由：`api/routes/sandbox.py` 新增 `GET /api/v1/sandbox/{session_id}/report`（在 CA2' 的 sandbox.py 中追加，不新建文件）
- 非必要不新建文件：若 CA2' 已在 sandbox.py 中包含报告端点，在此基础上追加，不得重复建文件

#### §4 Sequence Diagram（必填，文字版）
请描述：请求 `GET /sandbox/{session_id}/report` → sandbox.py → session store 查询 → ResearchSession → report_builder.py → 返回 JSON

#### §6 测试用例（最少 7 条）
- 含 session 未完成时的 404/400 处理
- 含报告 JSON 结构正确性验证
- 含 CSV 导出格式验证

---

### Task B5-2：CA4 交易参数调优引擎规格书

**输出文件**：`QWEN_SPEC_CA4_TRADING_OPTIMIZER.md`

**服务**：`services/decision/`  
**依赖**：CA2'（sanctuary sandbox 基础），CA3（可选，调优后自动生成报告）  
**注意**：`optuna_search.py` 已存在（XGBoost 超参调优），**CA4 复用 optuna_search.py 的 Trial 机制，扩展目标函数为交易绩效指标（Sharpe/回撤）**

#### 必须回答的问题
- `optuna_search.py` 当前优化的是什么？用的是什么目标函数？CA4 如何扩展而非重写？
- 调优的"交易参数"具体指哪些？（止损比例、仓位比例、持仓周期等）**必须给出参数清单**

#### §2 锚点声明
- 已存在：`research/optuna_search.py`（扩展，非新建）、`research/sandbox_engine.py`（CA2' 产出）
- 修改：`research/optuna_search.py`（新增 `trading_objective()` 函数，复用 sandbox_engine 评估调优 trial）
- 新建路由端点：在 `api/routes/sandbox.py` 追加 `POST /api/v1/sandbox/{session_id}/optimize`

#### §6 测试用例（最少 7 条）
- 含 optuna trial 调用 sandbox_engine 的 mock 验证
- 含调优完成后参数写回 ResearchSession 的验证

---

### Task B5-3：CB3 全 A 股选股引擎 + Benchmark 规格书

**输出文件**：`QWEN_SPEC_CB3_STOCK_SCREENER.md`

**服务**：`services/decision/`  
**依赖**：CB2'（stock sandbox 基础，才能按因子跑回测评分）  
**目标**：全 A 股排名打分 → 按 Sharpe/回撤/胜率加权排名 → 每日输出 Top-N 候选

#### 必须回答的问题
- 全 A 股数量级？如何批量获取股票代码列表？（通过 data API 还是本地 universe 文件？**明确一种方案**）
- Benchmark 的基准是什么？沪深300（000300.SH）or 全A等权？

#### §2 锚点声明
- 已存在：`research/sandbox_engine.py`（CB2' 产出，提供 stock backtest 能力）
- 新建：`research/stock_screener.py`（批量跑分 + 排名逻辑）
- 新建：`research/universe_loader.py`（股票 universe 加载，从 data API 或本地缓存）
- 新建路由端点：`api/routes/sandbox.py` 追加 `POST /api/v1/research/screener/run`

#### §4 Sequence Diagram（必填）
请描述：`POST /screener/run` → screener.py → universe_loader → 循环调用 sandbox_engine → 收集 metrics → 排名 → 返回 Top-N

#### §6 测试用例（最少 8 条）
- 含 universe 为空时的处理
- 含单支股票跑分 mock
- 含排名逻辑验证（Sharpe 加权）
- 含 benchmark 对比计算验证

---

### Task B5-4：CF2 邮件 + 看板 YAML 导入规格书

**输出文件**：`QWEN_SPEC_CF2_YAML_IMPORT.md`

**服务**：`services/decision/`（单服务，无跨服务）  
**依赖**：C0-3（策略导入解析器必须已完成，CF2 通过 C0-3 的 `StrategyImporter` 做解析）  
**目标**：两个入口（邮件 IMAP 拉取 + 看板 HTTP 上传）→ 共用 C0-3 解析 → 入库 → 飞书反馈

#### 必须回答的问题
- 邮件 YAML 导入：是主动 IMAP 轮询还是 SMTP webhook？以及轮询频率（建议每 15 分钟）？
- 看板上传：是 `multipart/form-data` 文件上传还是 JSON 内体传递 YAML 字符串？**推荐后者**

#### §2 锚点声明
- 已存在（C0-3 产出）：策略导入解析器相关文件（具体文件名需读取 C0-3 规格书确认）
- 新建：`api/routes/import.py`（看板 YAML 上传端点 `POST /api/v1/import/yaml`）
- 新建：`core/email_poller.py`（IMAP 邮件轮询服务）
- 修改：`api/app.py`（注册 `import_router`）

> ⚠️ `email_poller.py` 中的 IMAP 凭证必须从 `.env` 中读取（`JBT_IMAP_HOST`/`JBT_IMAP_USER`/`JBT_IMAP_PASS`），**不得硬编码任何邮件配置**。

#### §6 测试用例（最少 7 条）
- 含 YAML 格式有效/无效验证
- 含邮件轮询无新邮件时的 idle 行为
- 含飞书通知发送成功/失败的 mock
- 含重复导入同一 strategy_id 的幂等性验证

---

### Task B5-5：Batch-5 端到端验收场景

**输出文件**：`QWEN_E2E_ACCEPTANCE_BATCH5.md`

#### §1 CA3 验收场景
1. 完成 CA2' sandbox 跑一次回测 → 调用 `/sandbox/{session_id}/report` → 返回含 sharpe/max_drawdown/equity_curve 字段的 JSON ✅
2. session_id 不存在 → 返回 404，error_code 清晰 ✅

#### §2 CA4 验收场景
1. 调用 `POST /sandbox/{session_id}/optimize`（trials=10）→ optuna 完成 → 返回 best_params + best_sharpe ✅
2. sandbox 未完成时调用 optimize → 返回 400 ✅

#### §3 CB3 验收场景
1. `POST /research/screener/run`（universe=200只）→ 完成排名 → 返回 Top-30 含 symbol + score + rank ✅
2. universe 空列表 → 返回 400 + 明确错误 ✅

#### §4 CF2 验收场景
1. `POST /import/yaml`（合法 YAML body）→ C0-3 解析通过 → 入库 → 飞书通知"导入成功" ✅
2. `POST /import/yaml`（非法 YAML）→ 返回 422 + 飞书通知"导入失败"（含原因）✅
3. 邮件轮询：模拟收到含合法 YAML 的邮件 → 自动触发导入 → 飞书通知 ✅

#### §5 Phase C 进度快照更新
更新 `QWEN_PHASE_C_STEP3_REPORT.md` §3 优先级表中状态列：
- `Batch-4 规格完成` → CA2'/CB2'/CG3/CA6
- `Batch-5 规格完成` → CA3/CA4/CB3/CF2

---

## 输出要求

| 输出文件 | 最低行数 |
|----------|---------|
| `QWEN_SPEC_CA3_SANDBOX_REPORT.md` | 140 行 |
| `QWEN_SPEC_CA4_TRADING_OPTIMIZER.md` | 160 行 |
| `QWEN_SPEC_CB3_STOCK_SCREENER.md` | 160 行 |
| `QWEN_SPEC_CF2_YAML_IMPORT.md` | 150 行 |
| `QWEN_E2E_ACCEPTANCE_BATCH5.md` | 120 行 |

**所有文件输出到** `docs/handoffs/qwen-audit-collab/`

---

## 完成后提交

创建 `QWEN_BATCH5_COMPLETE.md`，包含 5 个文件路径、自评分（5 维度）、自查清单（重点检查 CA3/CA4 是否引用了正确的 CA2' sandbox_engine 方法名）。
