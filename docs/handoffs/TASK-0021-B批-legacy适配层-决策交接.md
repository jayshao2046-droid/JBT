# TASK-0021-B 批-legacy 适配层-决策交接单

【任务 ID】TASK-0021 B 批
【执行 Agent】决策 Agent
【时间】2026-04-07
【状态】✅ 实现完成，待项目架构师终审
【关联 Token】tok-746b5b6d-0e58-447a-847e-f35ff6be0e1a
【Review ID】REVIEW-TASK-0021-B

---

## 一、文件清单

| 文件路径 | 状态 | 说明 |
|---|---|---|
| `integrations/legacy-botquant/decision/__init__.py` | ✅ 新建 | 适配层公开接口导出 |
| `integrations/legacy-botquant/decision/adapter.py` | ✅ 新建 | 核心适配器，`from_legacy_dict` 转换链路 |
| `integrations/legacy-botquant/decision/input_mapper.py` | ✅ 新建 | 策略/信号字段名映射器 |
| `integrations/legacy-botquant/decision/signal_compat.py` | ✅ 新建 | 信号类型标准化与有效性验证 |

未修改任何其他文件。

---

## 二、实现摘要

### `__init__.py`
导出 `LegacyDecisionAdapter`、`LegacyInputMapper`、`LegacySignalCompat` 三个公开接口，所有工具模块从此入口引入。

### `signal_compat.py`
- `SIGNAL_TYPE_MAP`（常量）：10 种 legacy 信号类型 → JBT `"long"` / `"short"` / `"neutral"`，大小写不敏感，未知类型降级为 `"neutral"`。
- `SIGNAL_DIRECTION_MAP`（常量）：JBT 类型 → 整数方向（`1 / -1 / 0`）。
- `LegacySignalCompat.normalize_signal_type(legacy_type)` → 标准字符串。
- `LegacySignalCompat.normalize_signal_direction(jbt_signal_type)` → 整数方向。
- `LegacySignalCompat.is_valid_legacy_signal(raw)` → 布尔，验证 `signal_type` 或 `direction` 字段至少有一个存在且非空。

### `input_mapper.py`
- `STRATEGY_FIELD_MAP`（常量）：9 个 legacy 策略字段 → JBT 协议字段。
- `SIGNAL_FIELD_MAP`（常量）：9 个 legacy 信号字段 → JBT 协议字段。
- `LegacyInputMapper.map_strategy_fields(raw)` → 字段名重映射后的 dict。
- `LegacyInputMapper.map_signal_fields(raw)` → 字段名重映射后的 dict。
- 设计原则：先出现的字段优先（多对一映射不覆盖），未在映射表中的字段原样保留。

### `adapter.py`
- `LegacyDecisionAdapter(default_target, default_trace_prefix)` — 可配置默认目标和 trace 前缀。
- `from_legacy_dict(raw)` — 完整转换链路：字段名重映射 → 信号标准化 → 因子列表归一化 → market_context 归一化 → 填充元字段 → 输出符合 `decision_request.md` 契约的 dict。
- 缺失门禁字段（`factor_version_hash`、`research_snapshot_id`、`backtest_certificate_id`）填入占位值 `"legacy-unknown"` / `"legacy-placeholder"`，由下游 decision 服务自行决定是否通过门禁，适配层不越权判断。
- `_normalize_factors` 支持 `list[dict]`、`{name: value}` 平铺 dict、`None` 三种 legacy 因子格式。
- 输出扩展元字段 `_legacy_source: True` 和 `_legacy_signal_type`，供下游追踪来源。

---

## 三、字段映射表

### 策略字段映射（STRATEGY_FIELD_MAP）

| legacy 字段 | JBT 契约字段 | 备注 |
|---|---|---|
| `strategy_id` | `strategy_id` | 同名 |
| `strategy_name` | `strategy_id` | legacy 别名 |
| `name` | `strategy_id` | legacy 简写 |
| `version` | `strategy_version` | |
| `strategy_version` | `strategy_version` | 同名 |
| `status` | `status` | 同名 |
| `symbol` | `symbol` | 同名 |
| `instrument` | `symbol` | legacy CTP 别名 |
| `code` | `symbol` | legacy 简写 |

### 信号字段映射（SIGNAL_FIELD_MAP）

| legacy 字段 | JBT 契约字段 | 备注 |
|---|---|---|
| `signal_type` | `signal_type` | 同名，后续经 LegacySignalCompat 规范化 |
| `direction` | `signal_type` | legacy 方向字段 |
| `signal` | `signal_type` | legacy 简写 |
| `strength` | `signal_strength` | |
| `signal_strength` | `signal_strength` | 同名 |
| `confidence` | `signal_strength` | legacy 置信度别名 |
| `factor_values` | `factors` | legacy 因子数组 |
| `factor_value` | `factors` | legacy 单因子别名 |
| `factors` | `factors` | 同名 |

### 信号类型映射（SIGNAL_TYPE_MAP）

| legacy signal_type | JBT 标准 | 整数方向 |
|---|---|---|
| `BUY` / `LONG` / `OPEN_LONG` | `long` | `1` |
| `SELL` / `SHORT` / `OPEN_SHORT` | `short` | `-1` |
| `HOLD` / `NEUTRAL` / `CLOSE` / `EXIT` | `neutral` | `0` |
| （未知类型） | `neutral`（降级） | `0` |

---

## 四、质量验收结论

| 验收项 | 结果 |
|---|---|
| 4 个文件全部创建 | ✅ |
| `get_errors` 全部 0 errors | ✅ |
| 不依赖 Pydantic（只用标准库 + typing） | ✅ |
| 不 import services/** 或 J_BotQuant/** | ✅ |
| 所有方法有类型注解 | ✅ |
| 只读适配，不调用任何交易 API | ✅ |

---

## 五、无法按要求实现的项目

无。所有要求均已完整实现。

---

## 六、后续动作（由项目架构师执行）

1. 对本交接单内容进行终审（REVIEW-TASK-0021-B）。
2. 终审通过后，对以下 4 文件执行 lockback：
   - `integrations/legacy-botquant/decision/__init__.py`
   - `integrations/legacy-botquant/decision/adapter.py`
   - `integrations/legacy-botquant/decision/input_mapper.py`
   - `integrations/legacy-botquant/decision/signal_compat.py`
3. 更新 `docs/locks/` 记录。
