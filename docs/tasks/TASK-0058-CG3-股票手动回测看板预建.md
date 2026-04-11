# TASK-0058 — CG3 回测端股票手动回测与看板调整

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  
【状态】� Token 已签发（tok-b09df21e，等待 TASK-0055 完成后激活实施）

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0058 |
| 任务名称 | CG3 回测端股票手动回测与看板调整 |
| 所属阶段 | Phase C / Lane-B |
| 主责服务 | `services/backtest/` |
| 协同服务 | `services/data/`（股票 bars 数据）|
| 优先级 | P1 |
| 前置依赖 | **TASK-0055（CG2）完成** |
| 状态 | 📋 预建，未激活 |

## 激活条件

TASK-0055（CG2）经架构师终审并由 Jay.S 确认后自动激活。

## 任务背景

CG2 建立了期货策略的人工手动回测 + 审核链路（路由前缀 `/api/v1/backtest/manual/`）。  
CG3 在此基础上扩展股票策略支持，并调整 backtest_web 看板页面。

**路由前缀统一原则**（Atlas 强制）：  
- CG2 已建立 `/api/v1/backtest/manual/` 前缀  
- CG3 股票端点必须为 `/api/v1/backtest/manual/stock/`，**不另起 `/manual-backtest/` 前缀**

## 代码实情（Atlas 预查）

- `services/backtest/src/backtest/runner.py` ✅ 已存在（只调用，不修改）
- `services/backtest/src/api/routes/backtest.py` ✅ 已存在（期货回测路由基准）
- `services/backtest/src/api/routes/strategy.py` ✅ 已存在
- `services/backtest/src/api/app.py` ✅ 已存在（路由注册）
- `strategy_queue.py` ❌ 不存在（CG1 产出，**CG3 依赖此文件需声明 planned-placeholder**）
- `manual_runner.py` ❌ 不存在（CG2 产出，**CG3 依赖此文件需声明 planned-placeholder**）
- `api/routes/approval.py` ❌ 不存在（CG2 产出，**CG3 依赖此文件需声明 planned-placeholder**）

## 实现范围（最小白名单草案，待架构师确认）

### 新建文件

| 文件路径 | 说明 |
|----------|------|
| `services/backtest/src/backtest/stock_runner.py` | 股票手动回测执行器（封装 data API 股票 bars 拉取 + local_engine 调用）|
| `services/backtest/src/api/routes/stock_approval.py` | 股票回测审核路由（`POST /api/v1/backtest/manual/stock/run`，`POST /api/v1/backtest/manual/stock/{id}/approve`）|
| `tests/backtest/api/test_stock_approval.py` | 股票审核路由测试 |

### 修改文件

| 文件路径 | 变更摘要 |
|----------|---------|
| `services/backtest/src/api/app.py` | 注册 `stock_approval_router` |

### Planned-placeholder（依赖，不创建）

| 文件 | 说明 |
|------|------|
| `services/backtest/src/backtest/strategy_queue.py` | CG1 产出，CG3 使用队列读取能力 |
| `services/backtest/src/backtest/manual_runner.py` | CG2 产出，CG3 复用人工触发模式 |
| `services/backtest/src/api/routes/approval.py` | CG2 产出，CG3 复用审核状态机 |

## 新增路由规范

```
POST /api/v1/backtest/manual/stock/run         # 触发股票手动回测
GET  /api/v1/backtest/manual/stock/{run_id}    # 查询回测状态
POST /api/v1/backtest/manual/stock/{run_id}/approve  # 审核通过
POST /api/v1/backtest/manual/stock/{run_id}/reject   # 拒绝
```

响应扩展（股票专属字段）：
```json
{
  "run_id": "...",
  "status": "completed",
  "asset_type": "stock",
  "equity_curve": [{"date": "2025-01-01", "nav": 1.02}, ...],
  "sharpe": 1.45,
  "max_drawdown": 0.08,
  "annual_return": 0.23
}
```

## 验收标准

1. `POST /api/v1/backtest/manual/stock/run`（合法股票策略 + 时间区间）→ 返回 `run_id` ✅
2. 结果中包含 `equity_curve` 字段（逐日净值列表）✅
3. 审核通过 `/approve` → decision 服务回写状态（mock 验证）✅
4. 路由不与 CG2 期货端点冲突 ✅
5. `test_stock_approval.py` ≥6 条测试通过 ✅
