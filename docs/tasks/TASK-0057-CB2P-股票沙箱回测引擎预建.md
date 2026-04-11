# TASK-0057 — CB2' 股票沙箱回测引擎

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  
【状态】� Token 已签发（tok-00da5e7e，等待 TASK-0056 完成后激活实施）

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0057 |
| 任务名称 | CB2' 股票沙箱回测引擎 |
| 所属阶段 | Phase C / Lane-B |
| 主责服务 | `services/decision/` |
| 协同服务 | `services/data/`（通过 FactorLoader 取股票数据）|
| 优先级 | P1 |
| 前置依赖 | **TASK-0053（C0-2）完成 + TASK-0056（CA2'）完成**（需复用 CA2' 的 sandbox_engine.py）|
| 状态 | 📋 预建，未激活 |

## 激活条件

TASK-0056（CA2'）经架构师终审并由 Jay.S 确认后自动激活。  
CB2' **不新建 `sandbox_engine.py`**，在 CA2' 产出的基础上扩展股票分支。

## 任务背景

CB2' 是股票版沙箱，与 CA2' 期货沙箱共用同一个 `sandbox_engine.py` 文件，通过 `asset_type: "futures" | "stock"` 参数区分两条路径。  
主要扩展点：  
- A股 T+1 买入限制（当天买入不能当天卖出）  
- 涨跌停板限制（无法在涨停价买入 / 跌停价卖出）  
- 日线级别回测（股票使用 `stock_daily`，不用分钟K）  
- 成交量约束（成交量不足时限额成交）

## 实现范围（最小白名单草案，待架构师确认）

### 修改文件（无新增顶层文件）

| 文件路径 | 变更摘要 |
|----------|---------|
| `services/decision/src/research/sandbox_engine.py` | 新增 `asset_type="stock"` 分支：T+1/涨跌停/日线数据路径 |
| `tests/decision/research/test_sandbox_engine.py` | 追加股票路径测试（≥6 条），确认期货路径不回归 |

### 不新建的文件（重要）

- **不新建** `StockSandbox` 类或 `stock_sandbox_engine.py`
- **不新建** `StockDataProxy` / `StockExecutionEngine` / `StockRiskManager`
- 所有股票逻辑统一在 `sandbox_engine.py` 中通过 `asset_type` 条件分支实现

## 设计约束（Atlas 强制）

```
# 正确设计
class SandboxEngine:
    def run_backtest(
        self,
        strategy_config: dict,
        start: str,
        end: str,
        asset_type: Literal["futures", "stock"] = "futures",
        initial_capital: float = 1_000_000
    ) -> SandboxResult: ...
```

## 验收标准

1. `POST /api/v1/sandbox/run`（`asset_type="stock"`, 合法股票策略）→ 返回 `session_id` ✅
2. 股票路径正确应用 T+1 限制（回测记录中买入当天无卖出成交）✅
3. 涨停价买入请求被拦截（成交数量=0，附原因）✅
4. `asset_type="futures"` 路径不受 CB2' 修改影响（所有 CA2' 测试通过）✅
5. 测试追加后 `test_sandbox_engine.py` 总 case ≥14 条 ✅
