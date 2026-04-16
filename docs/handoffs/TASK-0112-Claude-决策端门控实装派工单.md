# TASK-0112 Claude 派工单 — 决策端模型口径修正与三级门控实装

【派工时间】2026-04-15
【复核人】Atlas
【执行 Agent】Claude-Code（决策 Agent 身份）

---

## 开工前必读

1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/决策提示词.md`
4. `docs/tasks/TASK-0112-decision-模型口径修正与三级门控实装.md`
5. `docs/reviews/TASK-0112-review.md`

---

## 架构事实（2026-04-15 Jay.S 确认，Ollama API 实查）

### Studio (192.168.31.142) 本地模型
| 模型 | 角色 | 时段 |
|------|------|------|
| deepcoder:14b | 策略调优 + 因子挖掘 | 夜间/非交易时段 |
| phi4-reasoning:14b | **L1 快审 + L2 深审**（只读研报 + K 线，见下方数据源规则） | 盘中 |
| qwen3:14b | 备用（不日常调度） | — |

### 数据源硬规则（2026-04-15 Jay.S 确认）

**phi4 和 deepcoder 只允许读取两类数据源，其余一律不看：**
1. **数据研究员报告**（qwen3 在 Alienware 生成）— 端点: `GET {DATA_API_URL}/api/v1/researcher/report/latest`
2. **K 线**（内盘 + 外盘 + 股票，分钟线 + 日线）— 端点: `GET {DATA_API_URL}/api/v1/bars` / `GET {DATA_API_URL}/api/v1/stocks/bars`

所有其他原始数据（新闻、公告、资金流、持仓等）由 qwen3 研究员在上游预先汇总成研报后供 phi4/deepcoder 使用，决策端代码**不得**直接读取其他数据 API。

**数据缺失报警规则**：
- 门控读取数据时如果**研报为空**或**K 线有缺失** → 通过飞书发 **P1 (orange ⚠️)** 报警
- 报警后门控行为：**降级继续**（K 线缺失用有的审，研报为空则只看 K 线），不 hold
- 使用已有 `services/decision/src/notifier/feishu.py` 的 `DecisionFeishuNotifier`

### Alienware (192.168.31.223) 数据研究员
| 模型 | 角色 |
|------|------|
| qwen3:14b | 预读采集数据 + 写研报（归属 services/data, TASK-0110） |

### L3 在线模型（DashScope API）
| 模型 | 角色 |
|------|------|
| Qwen3.6-Plus | 默认在线确认 |
| Qwen3-Max | 升级复核 |
| DeepSeek-V3.2 | 在线备援 |
| DeepSeek-R1 | 争议复核 |

### 不存在的模型（必须从代码中清除）
- ❌ Qwen2.5（signal.py L1 profile 错误引用）
- ❌ DeepSeek-R1-14B（.env 配置值，未安装）
- ❌ qwen3:14b 作为 pipeline auditor（已不在决策端职责，改 phi4）

---

## Batch A — 口径修正 + phi4 L1/L2 门控实装

**Token**: `tok-0a2faa03-6f93-4300-bb31-756af285b6bc`
**白名单（5 文件）**:
1. `services/decision/src/api/routes/signal.py`
2. `services/decision/src/llm/pipeline.py`
3. `services/decision/src/llm/gate_reviewer.py`（新建）
4. `services/decision/src/llm/context_loader.py`
5. `services/decision/tests/test_signal_gate.py`（新建）

### 具体要求

#### 1. `signal.py` — 修正 L1/L2 profile + 接入真实门控

**修正口径**：
```python
# 旧（错误）
_L1_MODEL_PROFILE = {
    "profile_id": "local-l1-qwen2.5-series",
    "model_name": "Qwen2.5",
    ...
}
_L2_MODEL_PROFILE = {
    "profile_id": "local-primary-qwen3-14b",
    "model_name": "Qwen3 14B",
    ...
}

# 新（正确）
_L1_MODEL_PROFILE = {
    "profile_id": "local-l1-phi4-reasoning",
    "model_name": "phi4-reasoning:14b",
    "deployment_class": "local",
    "route_role": "L1_gate_review",
}
_L2_MODEL_PROFILE = {
    "profile_id": "local-l2-phi4-reasoning",
    "model_name": "phi4-reasoning:14b",
    "deployment_class": "local",
    "route_role": "L2_deep_review",
}
```

**接入真实 LLM 门控**：
- 在 `review_signal()` 中，资格门禁（model_router + PublishGate）通过后，**调用 gate_reviewer 做真实 phi4 L1 快审**
- L1 快审通过 + signal≠0 后，**调用 gate_reviewer 做 L2 深审**
- 保留现有规则引擎逻辑作为**前置过滤**（live-trading 锁定、资格阻塞），只有通过前置的才进 LLM 审查
- `_decisions` 改为写入 `state_store`（解决内存丢失问题）

#### 2. `pipeline.py` — 修正 auditor 默认模型

```python
# 旧
self.auditor_model = os.getenv("OLLAMA_AUDITOR_MODEL", "qwen3:14b")
# 新
self.auditor_model = os.getenv("OLLAMA_AUDITOR_MODEL", "phi4-reasoning:14b")
```

#### 3. `gate_reviewer.py`（新建）— phi4 L1/L2 审查封装

```
class GateReviewer:
    L1 快审（~5s）:
      - 输入: strategy_id, symbol, signal, signal_strength, factors 列表
      - context: **5日日线K线**（从 context_loader 获取）
      - prompt: 简洁判断信号方向是否与近期趋势严重矛盾
      - 输出 JSON: {"pass": bool, "risk_flag": str, "confidence": float}
      
    L2 深审（~15s）:
      - 输入: L1 输出 + 完整因子列表 + market_context
      - context: **20日日线K线** + **最近60根分钟线** + **qwen3 研报摘要**（从 context_loader 获取）
      - prompt: 综合评估策略可执行性、风险水平、市场环境匹配度
      - 输出 JSON: {"approve": bool, "reasoning": str, "confidence": float, "risk_assessment": str}
    
    数据缺失处理:
      - 研报为空 → 飞书 P1 报警 + 降级为只看 K 线继续审
      - K线缺失 → 飞书 P1 报警 + 用现有数据降级审（count < 要求时标注 degraded）
      - 报警调用: DecisionFeishuNotifier (已有 notifier/feishu.py)
```

- 使用已有 `OllamaClient`，模型固定 `phi4-reasoning:14b`
- keep_alive:0 保持（每次调用后卸载）
- JSON 解析失败时返回保守默认值（pass=False）

#### 4. `context_loader.py` — 扩展门控上下文

在现有基础上新增：
- `get_l1_context(symbol)`: L1 快审上下文 — 拉取 **5日日线K线**
  - `GET {DATA_API_URL}/api/v1/bars?symbol={symbol}&duration=1d&count=5`
  - 期货 (内盘+外盘) 用 `/api/v1/bars`，股票用 `/api/v1/stocks/bars`（根据 symbol 前缀自动路由）
- `get_l2_context(symbol)`: L2 深审上下文 — 拉取 **20日日线K线** + **最近60根分钟线** + **研报摘要**
  - 日线: `GET {DATA_API_URL}/api/v1/bars?symbol={symbol}&duration=1d&count=20`
  - 分钟线: `GET {DATA_API_URL}/api/v1/bars?symbol={symbol}&duration=1m&count=60`
  - 研报: `GET {DATA_API_URL}/api/v1/researcher/report/latest`（TASK-0110 就绪前 graceful fallback 为空）
- 返回格式化的 context string 供 gate_reviewer prompt 注入
- **数据缺失检测**：如果任一数据源返回空/异常/条数不足，在 context 中标注 `[DATA_DEGRADED]` 并返回 `missing_sources` 列表供 gate_reviewer 触发飞书报警

#### 5. `test_signal_gate.py`（新建）

测试覆盖：
- L1 拒绝路径（mock phi4 返回 pass=False）
- L1 通过 → L2 拒绝路径
- L1 通过 → L2 通过 → approve 路径
- phi4 超时/JSON 解析失败 → 保守 hold
- 资格门禁阻塞不进入 LLM 审查
- 研报为空 → 飞书 P1 报警 + L2 降级只看 K 线
- K 线缺失 → 飞书 P1 报警 + 降级继续
- L1/L2 K 线窗口正确性（L1=5日日线, L2=20日日线+60根分钟线）

---

## Batch B — L3 在线模型接入

**Token**: `tok-08de1aff-99ac-44f3-af40-3f2899ccf1b7`
**白名单（4 文件）**:
1. `services/decision/src/llm/online_confirmer.py`（新建）
2. `services/decision/src/api/routes/signal.py`
3. `services/decision/src/api/routes/model.py`
4. `services/decision/tests/test_online_confirmer.py`（新建）

**前置**: Batch A 必须先完成

### 具体要求

#### 1. `online_confirmer.py`（新建）— DashScope L3 确认

```
class OnlineConfirmer:
    - 使用 DashScope OpenAI-compatible API (已在 .env 配置)
    - base_url: ONLINE_MODEL_BASE_URL (https://dashscope.aliyuncs.com/compatible-mode/v1)
    - api_key: ONLINE_MODEL_API_KEY
    - 默认模型: ONLINE_MODEL_DEFAULT (Qwen3.6-Plus)
    - 争议模型: ONLINE_MODEL_DISPUTE (DeepSeek-R1)
    
    confirm(decision_context) -> {confirmed: bool, reasoning: str, model_used: str}
    
    触发条件（任一满足才调 L3）:
    - signal_strength > 0.8（高强度信号需要在线确认）
    - L1 和 L2 confidence 差异 > 0.3（L1/L2 评分不一致）
    - risk_assessment 为 "high"（L2 标记高风险）
    
    降级策略:
    - DashScope API 失败/超时(30s) → 直接采纳 L2 结论
    - 默认模型失败 → 尝试 ONLINE_MODEL_BACKUP (DeepSeek-V3.2)
    - 全部失败 → 降级为 L2 结论 + 标记 "l3_degraded"
```

#### 2. `signal.py` — 在 L2 approve 后条件调 L3

- L2 approve + 触发条件 → 调 OnlineConfirmer
- L3 confirmed → 最终 approve（layer 标记为 "L3_online_confirm"）
- L3 not confirmed → hold（layer 标记为 "L3_online_reject"）
- L3 降级 → 采用 L2 结论（layer 标记为 "L2_local_review_l3_degraded"）

#### 3. `model.py` — online_models 不再硬编码空

```python
# 旧
"online_models": [],

# 新：读取 .env 配置
"online_models": [
    {"model_id": "online-default", "name": settings.online_model_default, "type": "online", "status": "configured"},
    {"model_id": "online-upgrade", "name": settings.online_model_upgrade, "type": "online", "status": "configured"},
    {"model_id": "online-backup", "name": settings.online_model_backup, "type": "online", "status": "configured"},
    {"model_id": "online-dispute", "name": settings.online_model_dispute, "type": "online", "status": "configured"},
],
```

#### 4. `test_online_confirmer.py`（新建）

测试覆盖：
- 触发条件满足 → 调 L3 → confirmed
- 触发条件满足 → 调 L3 → not confirmed → hold
- 触发条件不满足 → 跳过 L3 → 直接 L2 结论
- DashScope 超时 → 降级为 L2
- 默认模型失败 → 备援模型 fallback
- 全部失败 → 降级 + 标记 l3_degraded

---

## 执行顺序

1. **先执行 Batch A**（validate token tok-0a2faa03 → 实施 → 自校验 → 交接）
2. **再执行 Batch B**（validate token tok-08de1aff → 在 A 基础上实施 → 自校验 → 交接）

## 自校验要求

每批完成后：
1. 白名单文件 `get_errors = 0`
2. `cd services/decision && PYTHONPATH=. ../../.venv/bin/pytest tests/ -q` 全部通过
3. 提交交接单到 `docs/handoffs/`

## 禁止事项

- 不得修改 `.env` 或 `.env.example`（P0/禁区）
- 不得修改白名单外的任何文件
- 不得跨服务 import
- 不得修改 `shared/contracts/**`

---

## Batch C — 全自动研究流水线串联

**Token**：`tok-370db4de-07c8-4adb-a591-ea8cdc730bbb`  
**前置条件**：必须在 Batch A + Batch B 均完成并通过测试后才能执行

### 白名单文件（4 个）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/research/evening_rotation.py` | 修改 | 修复 `rotate()` 方法：改为调 `_score_stock(symbol, k_line_data)` 而非简单循环，传入5日日线K线数据 |
| `services/decision/src/research/optuna_search.py` | 修改 | 新增调度支持：`schedule_nightly(hour=21, minute=0)` 方法，支持每日21:00自动触发搜索 |
| `services/decision/src/llm/pipeline.py` | 修改 | 连通全流水线：`full_pipeline()` 末尾调用 `optuna_search.auto_optimize()` → `sandbox_engine.auto_backtest()` → 返回完整结果 dict |
| `services/decision/tests/test_research_pipeline.py` | 新建 | 全流水线集成测试：mock Optuna + SandboxEngine，验证串联调用与结果格式 |

### 关键实现要求

#### `evening_rotation.py` — 修复 rotate() 调用

```python
# 错误（当前）：直接用 symbol 字符串，没传 K 线数据
for symbol in self.watchlist:
    self._process(symbol)

# 正确（目标）：拉取5日日线后调 _score_stock
from ..data_client import DataClient  # 已有的数据客户端
for symbol in self.watchlist:
    k_data = DataClient.get_bars(symbol, period="daily", count=5)
    score = self._score_stock(symbol, k_data)
    self._emit_result(symbol, score)
```

#### `optuna_search.py` — 新增调度入口

```python
def schedule_nightly(self, hour: int = 21, minute: int = 0) -> None:
    """注册夜间定时搜索任务，由 scheduler 调用"""
    import schedule
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.run_search)

def auto_optimize(self) -> dict:
    """pipeline.py 调用的自动完整优化入口，返回最优参数集"""
    result = self.run_search()
    return {"best_params": result.best_params, "best_value": result.best_value}
```

#### `pipeline.py` — 连通 full_pipeline()

```python
def full_pipeline(self, symbol: str, context: dict) -> dict:
    # ... 已有 L1/L2/L3 门控逻辑 ...
    
    # Batch C 新增：串联 Optuna + Sandbox
    if gate_result.get("approved"):
        opt_result = self.optuna_search.auto_optimize()
        backtest_result = self.sandbox_engine.auto_backtest(
            symbol=symbol,
            params=opt_result["best_params"]
        )
        return {
            **gate_result,
            "optimization": opt_result,
            "backtest": backtest_result,
        }
    return gate_result
```

### 自校验要求

1. `get_errors` 白名单文件 = 0
2. `pytest tests/test_research_pipeline.py -v` 全部通过
3. `full_pipeline()` 返回包含 `optimization` + `backtest` 字段
