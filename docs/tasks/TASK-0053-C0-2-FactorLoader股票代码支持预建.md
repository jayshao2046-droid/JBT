# TASK-0053 — C0-2 FactorLoader 股票代码支持

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  
【状态】📋 预建档案（等待 C0-1 + C0-3 双完成后激活）

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0053 |
| 任务名称 | C0-2 FactorLoader 股票代码支持 |
| 所属阶段 | Phase C / Lane-B |
| 主责服务 | `services/decision/` |
| 协同服务 | `services/data/`（调用 C0-1 提供的 stock_bars API）|
| 优先级 | P1 |
| 前置依赖 | **TASK-0050（C0-1）+ TASK-0051（C0-3）双完成** |
| 状态 | 📋 预建，未激活 |

## 激活条件

当 TASK-0050 和 TASK-0051 均经过架构师终审并由 Jay.S 确认上线后，本任务自动激活。

## 任务背景

决策服务 `research/` 中的 FactorLoader 当前仅支持期货品种，  
需扩展以支持股票代码（symbol 格式如 `000001.SZ`），  
以便 CA2'（期货沙箱）和 CB2'（股票沙箱）消费股票因子数据。  
数据来源为 C0-1 提供的 `GET /api/v1/stocks/bars` 端点。

## 实现范围（最小白名单草案，待架构师确认）

### 修改文件

| 文件路径 | 变更摘要 |
|----------|---------|
| `services/decision/src/research/factor_loader.py` | 扩展支持股票 symbol 格式，新增 `load_stock_bars()` 方法 |

### 新建文件

| 文件路径 | 说明 |
|----------|------|
| `services/decision/src/research/stock_data_client.py` | 对 C0-1 stock_bars API 的 HTTP 客户端封装 |
| `tests/decision/research/test_stock_data_client.py` | 测试文件 |

### 禁区

- `shared/contracts/**`、`shared/python-common/**`
- `services/data/**`（data 服务由 C0-1 已实现，不再修改）
- `services/decision/src/research/` 中除 `factor_loader.py` 之外的文件

## 验收标准（草案）

1. `FactorLoader.load_stock_bars(symbol="000001.SZ", start=..., end=...)` 能正确调用 C0-1 API 并返回数据。
2. HTTP 客户端有重试机制（最多 3 次，间隔 1s）。
3. 单元测试覆盖：mock C0-1 API 响应，验证数据解析正确性。
4. 期货相关 FactorLoader 方法无回归。

## 依赖关系

- 前置：C0-1（已提供 stock_bars API）+ C0-3（已提供 StrategyImporter）
- 解锁：CA2' / CB2'（均依赖本任务）

---

状态历史：  
- 2026-04-11 Atlas 预建档案，等待 C0-1 + C0-3 完成后激活
