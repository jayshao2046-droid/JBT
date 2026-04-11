# TASK-0055 — CG2 人工手动回测 + 审核确认

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  
【状态】📋 预建档案（等待 TASK-0052 / CG1 完成后激活）

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0055 |
| 任务名称 | CG2 人工手动回测 + 审核确认 |
| 所属阶段 | Phase C / Lane-B |
| 主责服务 | `services/backtest/` |
| 协同服务 | `services/decision/`（接收审核确认结果）|
| 优先级 | P1 |
| 前置依赖 | **TASK-0052（CG1）完成**（需项目架构师预审 + Token）|
| 状态 | 📋 预建，未激活 |

## 激活条件

当 TASK-0052（CG1 策略导入队列）经过架构师终审并由 Jay.S 确认上线后，本任务自动激活。  
**注意**：CG2 需独立申请架构师预审 + Token。

## 任务背景

CG1 建立了策略导入队列后，CG2 目标是：  
1. 允许人工触发队列中的策略进行回测（manual trigger）  
2. 回测完成后提供审核界面（通过 API 返回结果供看板展示）  
3. 人工确认或拒绝回测结果  
4. 确认后信号进入下一环节（CA6 信号真闭环的前置）

## 实现范围（最小白名单草案，待架构师确认）

### 新建文件

| 文件路径 | 说明 |
|----------|------|
| `services/backtest/src/backtest/manual_runner.py` | 人工触发回测执行器（从队列取策略，调用 runner.py）|
| `services/backtest/src/api/routes/approval.py` | 审核确认端点（GET 结果 / POST 确认/拒绝）|
| `tests/backtest/api/test_approval.py` | 测试文件 |

### 修改文件

| 文件路径 | 变更摘要 |
|----------|---------|
| `services/backtest/src/main.py` | 注册 approval router |
| `services/backtest/src/backtest/strategy_queue.py` | 添加 `status: running` 状态变更接口（由 manual_runner 调用）|

### 禁区

- `services/backtest/src/backtest/runner.py`（核心执行引擎只调用，不修改）
- `shared/contracts/**`、`shared/python-common/**`
- 任何 decision 服务文件（通过 HTTP 协同）

## 验收标准（草案）

1. `POST /api/v1/backtest/manual/run?queue_id=xxx` 触发人工回测，返回 `run_id`。
2. `GET /api/v1/backtest/approval/{run_id}` 返回回测结果摘要。
3. `POST /api/v1/backtest/approval/{run_id}/approve` 确认，`/reject` 拒绝，状态持久化到内存。
4. `runner.py` 现有逻辑无回归。

## 依赖关系

- 前置：CG1（策略导入队列已实现）
- 解锁：CG3（回测端股票手动回测与看板调整）、CA6（信号真闭环）

---

状态历史：  
- 2026-04-11 Atlas 预建档案，等待 CG1 完成 + Token 签发后激活
