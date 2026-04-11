# TASK-0056 — CA2' 期货沙箱回测引擎

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  
【状态】� Token 已签发（tok-b73294b3，等待 TASK-0053 完成后激活实施）

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0056 |
| 任务名称 | CA2' 期货沙箱回测引擎 |
| 所属阶段 | Phase C / Lane-B |
| 主责服务 | `services/decision/` |
| 协同服务 | `services/data/`（通过 FactorLoader 取数）|
| 优先级 | P1 |
| 前置依赖 | **TASK-0053（C0-2 FactorLoader 股票支持）完成** |
| 状态 | 📋 预建，未激活 |

## 激活条件

当 TASK-0053（C0-2）经架构师终审并由 Jay.S 确认后，本任务自动激活。  
**注意**：CA2' 属单服务（decision 内部），不需要跨服务 Token。

## 任务背景

决策服务需要一个内置的快速回测沙箱用于研究中心的策略迭代：  
- **与 backtest 服务的区别**：沙箱为轻量内联计算（毫秒级）；backtest 为独立服务完整引擎（分钟级）  
- 沙箱结果不直接进策略池，必须经过 backtest 端人工二次复核（CG1/CG2）  
- CA2' 期货沙箱 + CB2' 股票沙箱共用同一个 `sandbox_engine.py`，通过 `asset_type` 参数区分

## 实现范围（最小白名单草案，待架构师确认）

### 新建文件

| 文件路径 | 说明 |
|----------|------|
| `services/decision/src/research/sandbox_engine.py` | 沙箱核心引擎（支持 `asset_type: "futures" \| "stock"`）|
| `services/decision/src/api/routes/sandbox.py` | 沙箱路由（`POST /api/v1/sandbox/run`，`GET /api/v1/sandbox/{session_id}`）|
| `tests/decision/research/test_sandbox_engine.py` | 沙箱引擎单元测试 |

### 修改文件

| 文件路径 | 变更摘要 |
|----------|---------|
| `services/decision/src/api/app.py` | 注册 `sandbox_router` |

### 代码实情（Atlas 预查）

- `services/decision/src/research/factor_loader.py` ✅ 已有 httpx，`_fetch_bars()` 方法可直接复用
- `services/decision/src/research/session.py` ✅ 已有 `ResearchSession`（dataclass），`sandbox_engine` 可复用
- `services/decision/src/research/trainer.py` ✅ 已有 `XGBoostTrainer`（独立模块，不干预沙箱）
- `services/decision/src/api/app.py` ✅ 当前注册 5 个 router，追加 sandbox_router 即可
- `strategy_queue.py` ❌ 不存在（CG1 产出），**sandbox_engine 不依赖此文件**

## 验收标准

1. `POST /api/v1/sandbox/run`（`asset_type="futures"`, 合法策略参数）→ 返回 `session_id` 和 `status: queued` ✅
2. `GET /api/v1/sandbox/{session_id}` → 回测完成后返回 `sharpe`, `max_drawdown`, `equity_curve` ✅
3. `sandbox_engine.py` 通过 `factor_loader._fetch_bars()` 取期货数据，不直接调用期货 API ✅
4. `asset_type="stock"` 调用沙箱时，期货路径不回归（CB2' 验证点）✅
5. `tests/decision/research/test_sandbox_engine.py` 通过（≥8 条 case）✅
