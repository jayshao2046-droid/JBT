# TASK-0052 — CG1 回测端策略导入队列

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0052 |
| 任务名称 | CG1 回测端策略导入队列 |
| 所属阶段 | Phase C / Lane-A |
| 主责服务 | `services/backtest/` |
| 协同服务 | `services/decision/`（策略源） |
| 优先级 | P1 |
| 状态 | 🔓 Token 已签发（tok-5d4f2cca） |

## 任务背景

回测服务 `api/routes/strategy.py` 已存在策略 CRUD 路由，  
但缺少从决策服务接收策略并进入回测队列的导入机制（import queue）。  
是 CG2（人工手动回测 + 审核确认）的前置依赖。  
本任务无前置依赖，可与 C0-1 / C0-3 并行。

## 实现范围（最小白名单）

### 新建文件

| 文件路径 | 说明 |
|----------|------|
| `services/backtest/src/backtest/strategy_queue.py` | 策略导入队列（enqueue / dequeue / list / status） |
| `services/backtest/src/api/routes/strategy_import.py` | 策略导入 HTTP 端点 |

### 修改文件

| 文件路径 | 变更摘要 |
|----------|---------|
| `services/backtest/src/main.py` | 注册 strategy_import router |

### 禁区（不得触及）

- `shared/contracts/**`
- `shared/python-common/**`
- `.github/**`
- `docker-compose.dev.yml`
- 任一真实 `.env`
- `services/backtest/src/backtest/runner.py`（回测执行核心，不在本任务范围）
- `services/backtest/src/api/routes/strategy.py`（现有路由不改动）

## 功能需求

```
POST /api/v1/backtest/strategy/import
  Body: { strategy_id, source: "decision" | "manual", strategy_data: {...} }
  返回: { queue_id, status: "queued" | "error" }

GET /api/v1/backtest/strategy/queue
  返回: [{ queue_id, strategy_id, status, created_at }]
```

队列实现：内存队列（Phase C 初版），无需持久化到数据库。

## 验收标准

1. `POST /api/v1/backtest/strategy/import` 返回 `queue_id`，状态为 `queued`。
2. `GET /api/v1/backtest/strategy/queue` 返回队列列表。
3. 原有 `strategy.py` 路由（GET/POST/DELETE）无回归。
4. 新增文件有单元测试覆盖。
5. 无跨服务直接 import，通过 HTTP 与 decision 服务协同。

## 依赖关系

- 无前置依赖（Lane-A 并行）
- 解锁：CG2（依赖本任务完成）

---

状态历史：  
- 2026-04-11 Atlas 建档，等待架构师预审
