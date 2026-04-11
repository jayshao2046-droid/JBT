# Atlas → Qwen Batch-2 派发单

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  

---

## ⚠️ 强制质量要求（本批次起全面执行）

1. **零瑕疵原则**：提交前必须自查，100 分目标，低于 80 分 Atlas 将暂停流程向 Jay.S 上报。
2. **锚点声明义务**：每份规格书必须有独立章节 §锚点声明，列出：已存在文件 / 新建文件 / planned-placeholder。
3. **绝对禁止**：将 planned-placeholder 文件写成"已存在锚点"。
4. **依赖闭环义务**：提交前必须对照 `QWEN_PHASE_C_STEP3_REPORT.md` §4 并行关系图，确认依赖声明一致。
5. **格式义务**：每份文档的所有表格必须无空单元格，所有代码块必须标注语言。

---

## 输入材料（必须在执行前完整阅读）

| 材料 | 路径 |
|------|------|
| Phase C 全量矩阵 | `docs/handoffs/qwen-audit-collab/ATLAS_TO_QWEN_PHASE_C_STEP1.md` |
| 首批候选分析（已含 Atlas 修正）| `docs/handoffs/qwen-audit-collab/ATLAS_PHASE_C_STEP2_REVIEW.md` |
| 全量部署编排（已 Atlas 直修无瑕）| `docs/handoffs/qwen-audit-collab/QWEN_PHASE_C_STEP3_REPORT.md` |
| Atlas–Qwen SOP | `docs/handoffs/qwen-audit-collab/ATLAS_QWEN_SOP.md` |
| 数据服务主入口 | `services/data/src/main.py` |
| 数据服务 storage | `services/data/src/data/storage.py` |
| 决策服务 publish 目录 | `services/decision/src/publish/` |
| 回测服务 strategy 路由 | `services/backtest/src/api/routes/strategy.py` |
| 回测服务 backtest 目录 | `services/backtest/src/backtest/` |

---

## 子任务清单（共 5 项，全部输出到 `docs/handoffs/qwen-audit-collab/`）

---

### Task B2-1：C0-1 实施规格书

**输出文件**：`QWEN_SPEC_C0-1_STOCK_BARS_API.md`

**内容要求**：

#### §1 任务摘要
- 目标：在 `services/data/` 新增股票 bars 查询 API，复用现有 stock_minute 存储。

#### §2 锚点声明（必填，格式如下）
```
已存在：
  - services/data/src/main.py（主 FastAPI 应用，现有路由均可作为参考模式）
  - services/data/src/data/storage.py（存储层，可复用读取逻辑）
  - services/data/src/utils/config.py

新建（本任务产出）：
  - services/data/src/api/__init__.py
  - services/data/src/api/routes/__init__.py
  - services/data/src/api/routes/stock_bars.py
  - tests/data/api/test_stock_bars.py

planned-placeholder（不在本任务范围，不得引用）：
  - （无，此任务不依赖任何 placeholder）
```

#### §3 接口规范
给出完整路由定义（含路由路径、HTTP 方法、Query 参数名/类型/必填、响应 JSON schema）。

#### §4 数据读取设计
- stock_minute 目录结构说明（从 `main.py` 中的 `SOURCE_OUTPUT_DIRS["stock_minute"]` = `"stock_minute"` 推导）
- 读取逻辑伪代码（函数签名级别，不需要完整实现）

#### §5 错误处理清单
列出所有可能错误场景 → HTTP 状态码 → 响应体格式

#### §6 单元测试用例设计
表格形式，列：用例ID、前置条件、输入、预期输出、测试类型（happy/boundary/error）
最少 8 条用例。

#### §7 依赖关系确认
- 本任务无前置依赖（Lane-A 首发）
- 解锁：CB5（依赖本任务）、C0-2（依赖本任务 + C0-3 双完成）

---

### Task B2-2：C0-3 实施规格书

**输出文件**：`QWEN_SPEC_C0-3_STRATEGY_IMPORTER.md`

**内容要求**：与 B2-1 相同的章节结构（§1~§7），针对以下内容：

- 目标：在 `services/decision/src/publish/` 新增 `strategy_importer.py` + `yaml_importer.py`
- 读取 `services/decision/src/publish/` 现有文件（`executor.py`, `gate.py`, `sim_adapter.py`），说明新文件如何与现有模块协作（不改动现有文件）
- `strategy_importer.py` 中的 `StrategyModel` 使用 decision 服务本地 `model/` 目录定义（不引用 `shared/contracts`，请先读取 `services/decision/src/model/` 目录，说明具体使用哪个类）
- YAML schema 最小字段：`name, symbol, exchange, direction, entry_rules, exit_rules, risk_params`
- 最少 6 条单元测试用例（含 schema 校验失败场景）

---

### Task B2-3：CG1 实施规格书

**输出文件**：`QWEN_SPEC_CG1_STRATEGY_QUEUE.md`

**内容要求**：与 B2-1 相同的章节结构（§1~§7），针对以下内容：

- 目标：在 `services/backtest/` 新增策略导入队列（内存实现，无持久化）
- 读取 `services/backtest/src/api/routes/strategy.py` 现有路由，说明新路由如何避免路径冲突
- 读取 `services/backtest/src/backtest/` 目录现有文件，说明 `strategy_queue.py` 在模块中的位置
- `main.py` 需要注册新路由，给出精确的 `app.include_router(...)` 语句
- 最少 6 条单元测试用例（含队列满/空/重复入队场景）

---

### Task B2-4：三任务统一接口约定草案

**输出文件**：`QWEN_INTERFACE_DRAFT_BATCH2.md`

**内容要求**：

#### §1 C0-1 ↔ CB5 接口约定
- C0-1 提供的数据格式规范（field names, types, null behavior）
- CB5 消费 C0-1 API 时需要的参数列表
- 任何字段不匹配的风险说明

#### §2 C0-1 ↔ C0-2 接口约定
- C0-1 完成后，C0-2（FactorLoader 股票代码支持）如何调用 stock_bars API
- 参数传递规范

#### §3 CG1 ↔ CG2 接口约定
- CG1 队列的 `queue_id` 格式规范（UUID/自增/hash）
- CG2 消费队列时需要的接口方法（poll / ack / reject）
- 状态机：queued → running → completed / failed

#### §4 跨任务数据类型统一映射表
列出三个任务中共同涉及的字段（如 `symbol`, `exchange`, `datetime`），统一类型定义。

---

### Task B2-5：端到端验收场景清单

**输出文件**：`QWEN_E2E_ACCEPTANCE_BATCH2.md`

**内容要求**：

#### §1 C0-1 验收场景（最少 5 条）
表格：场景ID、描述、操作步骤、预期结果、验收方式（curl/pytest/手工）

#### §2 C0-3 验收场景（最少 4 条）
同上格式。

#### §3 CG1 验收场景（最少 4 条）
同上格式。

#### §4 回归测试覆盖确认
- 列出 data 服务哪些现有路由需要在 C0-1 实施后做回归验证
- 列出 backtest 服务哪些现有路由需要在 CG1 实施后做回归验证

---

## 输出要求

| 输出文件 | 最低行数 | 截止时间 |
|----------|---------|---------|
| `QWEN_SPEC_C0-1_STOCK_BARS_API.md` | 150 行 | 本批次内 |
| `QWEN_SPEC_C0-3_STRATEGY_IMPORTER.md` | 130 行 | 本批次内 |
| `QWEN_SPEC_CG1_STRATEGY_QUEUE.md` | 130 行 | 本批次内 |
| `QWEN_INTERFACE_DRAFT_BATCH2.md` | 100 行 | 本批次内 |
| `QWEN_E2E_ACCEPTANCE_BATCH2.md` | 120 行 | 本批次内 |

**所有文件均输出到**：`docs/handoffs/qwen-audit-collab/`

---

## Atlas 将根据以下评分维度审核（100分制）

| 维度 | 分值 |
|------|------|
| 完整性（所有章节无缺项）| 20 |
| 锚点真实性（无误标）| 20 |
| 接口清晰度（签名/schema 无歧义）| 20 |
| 依赖链准确性（与 Step3 图一致）| 20 |
| 测试用例设计（happy+边界+异常）| 20 |

**低于 80 分将暂停流程，向 Jay.S 汇报详细扣分原因。**

---

## 完成后提交方式

完成后在 `docs/handoffs/qwen-audit-collab/` 目录下创建：
`QWEN_BATCH2_COMPLETE.md`，内容包含：
1. 5 个输出文件的路径列表
2. Qwen 自评分（按上述 5 维度各自评分，附理由）
3. 自查清单确认（锚点声明已填 ✅ / 依赖与 Step3 图一致 ✅ / 无空表格单元格 ✅）
