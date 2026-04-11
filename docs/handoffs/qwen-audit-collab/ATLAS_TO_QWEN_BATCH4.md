# Atlas → Qwen Batch-4 派发单

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  

---

## ⏳ 本批次激活条件

**必须等待以下全部完成并经 Jay.S 确认后启动：**

| 前置任务 | 解锁项 |
|----------|--------|
| TASK-0053 C0-2 完成 | 解锁 CA2' + CB2' |
| TASK-0054 CB5 完成 | 解锁 CB6 |
| TASK-0055 CG2 完成 | 解锁 CG3 + CA6 |

---

## ⚠️ 强制质量要求（同 Batch-2/3，继续执行）

1. 零瑕疵原则，100 分目标，低于 80 分 Atlas 暂停。
2. §锚点声明 必填；已存在 / 新建 / planned-placeholder 三类严格分开。
3. 路由注册在 `api/app.py`，不是 `main.py`。
4. 跨服务任务必须显式标注"需独立 Token"。
5. **新增质量要求**：每个规格书 §4 数据流设计必须包含完整的 sequence diagram（文字版），描述请求从 API 层到数据层的完整调用链。

---

## 输入材料

| 材料 | 路径 |
|------|------|
| SOP | `docs/handoffs/qwen-audit-collab/ATLAS_QWEN_SOP.md` |
| 全量编排 | `docs/handoffs/qwen-audit-collab/QWEN_PHASE_C_STEP3_REPORT.md` |
| C0-2 规格书（Atlas 审后版）| `docs/handoffs/qwen-audit-collab/QWEN_SPEC_C0-2_FACTOR_LOADER_STOCK.md` |
| CG2 规格书（Atlas 审后版）| `docs/handoffs/qwen-audit-collab/QWEN_SPEC_CG2_MANUAL_BACKTEST.md` |
| factor_loader.py | `services/decision/src/research/factor_loader.py` |
| decision api/app.py | `services/decision/src/api/app.py` |
| backtest api/app.py | `services/backtest/src/api/app.py` |
| backtest runner.py | `services/backtest/src/backtest/runner.py` |

---

## 子任务清单（共 5 项）

---

### Task B4-1：CA2' 期货沙箱回测引擎规格书

**输出文件**：`QWEN_SPEC_CA2P_FUTURES_SANDBOX.md`

**服务**：`services/decision/`  
**依赖**：C0-2（FactorLoader 已支持股票）  
**特点**：决策服务内部沙箱，不直接调用 backtest 服务，是独立的 "快速内循环" 回测

#### 必须回答的问题
- `ca2p` 沙箱与 backtest 服务的 `runner.py` 有何本质区别？（沙箱 = 轻量内联计算；backtest = 独立服务完整引擎）
- 数据来源：直接调用 `FactorLoader` 还是再调用一次 C0-1 API？

#### §2 锚点声明
- 已存在：`factor_loader.py`、`research/trainer.py`、`research/session.py`
- 新建：`services/decision/src/research/sandbox_engine.py`（期货沙箱核心）
- 修改：`services/decision/src/api/app.py`（注册沙箱路由）
- 新建路由：`services/decision/src/api/routes/sandbox.py`

#### §6 测试用例（最少 8 条）

---

### Task B4-2：CB2' 股票沙箱回测引擎规格书

**输出文件**：`QWEN_SPEC_CB2P_STOCK_SANDBOX.md`

**服务**：`services/decision/`  
**依赖**：C0-2（FactorLoader 已支持股票）  
**与 CA2' 的关系**：可复用 `sandbox_engine.py` 的期货逻辑，扩展股票标的支持

#### §2 锚点声明
- 复用 CA2' 的 `sandbox_engine.py`（已新建），扩展股票 symbol 分支
- 修改：`sandbox_engine.py`（接受 `asset_type: "futures" | "stock"` 参数）
- **不新建独立引擎文件**，说明 CA2'/CB2' 合并为一个引擎的设计理由

#### §6 测试用例（最少 6 条，重点交集验证 CA2' 期货路径不回归）

---

### Task B4-3：CG3 回测端股票手动回测与看板调整规格书

**输出文件**：`QWEN_SPEC_CG3_STOCK_BACKTEST_BOARD.md`

**服务**：`services/backtest/`  
**依赖**：CG2（已有人工手动回测 + 审核）  
**目标**：在 CG2 基础上扩展股票支持，并返回适合看板展示的结果结构

#### §3 接口规范
- `POST /api/v1/backtest/manual/run-stock`（基于 CG2 的 run 端点扩展）
- 响应中增加 `equity_curve`（权益曲线，每日净值列表）

#### §6 测试用例（最少 6 条）

---

### Task B4-4：CA6 信号真闭环 → sim-trading 接口规格书

**输出文件**：`QWEN_SPEC_CA6_SIGNAL_LOOP.md`

**服务**：`services/decision/`（信号生成）+ `services/sim-trading/`（接收端）  
**依赖**：CG2（回测通过才能进入实盘信号）  
**⚠️ 跨服务**：需独立 Token（两个服务各一个白名单）

#### §2 锚点声明
- 先读取 `services/sim-trading/src/` 目录结构，列出真实存在的接收端文件
- 若 sim-trading 接收信号的端点不存在，标记为 planned-placeholder 并说明依赖链

#### §3 接口约定
- Decision 侧：`POST /signals/{signal_id}/dispatch`（发送到 sim-trading）
- Sim-trading 侧：`POST /api/v1/signals/receive`（接收信号）
- 消息体格式规范（统一字段：signal_id, strategy_id, symbol, direction, quantity, price, timestamp）

#### §6 测试用例（最少 8 条，含跨服务 mock 场景）

---

### Task B4-5：Batch-4 端到端验收场景 + 完整 Phase C 进度快照

**输出文件**：`QWEN_E2E_ACCEPTANCE_BATCH4.md`

#### §1~§4 各任务验收场景（同 Batch-2/3 格式）

#### §5 Phase C 完成进度快照（新增）
**更新** `QWEN_PHASE_C_STEP3_REPORT.md` §3 优先级表中每个任务的"当前状态"列：
- `Batch-2 规格完成` → C0-1/C0-3/CG1
- `Batch-3 规格完成` → C0-2/CB5/CG2
- `Batch-4 规格完成` → CA2'/CB2'/CG3/CA6

---

## 输出要求

| 输出文件 | 最低行数 |
|----------|---------|
| `QWEN_SPEC_CA2P_FUTURES_SANDBOX.md` | 170 行 |
| `QWEN_SPEC_CB2P_STOCK_SANDBOX.md` | 140 行 |
| `QWEN_SPEC_CG3_STOCK_BACKTEST_BOARD.md` | 150 行 |
| `QWEN_SPEC_CA6_SIGNAL_LOOP.md` | 180 行 |
| `QWEN_E2E_ACCEPTANCE_BATCH4.md` | 140 行 |

**所有文件输出到** `docs/handoffs/qwen-audit-collab/`

---

## 完成后提交

创建 `QWEN_BATCH4_COMPLETE.md`，包含 5 个文件路径、自评分（5 维度）、自查清单。
