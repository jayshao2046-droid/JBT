# sim-trading

## 角色

JBT 模拟交易服务，唯一目标是对接 SimNow 并完成模拟交易执行。

## 固定边界

1. 只负责 SimNow 模拟交易。
2. 不使用内存模拟交易。
3. 不使用 TqSim 作为模拟盘。
4. 自己维护订单、成交、持仓、资金和风控执行链。
5. 只通过 API 接收决策端或人工操作指令。

## 端口

- 8101

## 未来目录职责

- `src/`: API、交易执行、账本、风控
- `tests/`: 模拟交易服务测试
- `configs/`: SimNow、风控、通知配置

## 外部依赖

- 上游：decision
- 下游：dashboard
- 兼容层：legacy-botquant

## 快速启动（骨架阶段）

```bash
# 复制环境模板
cp .env.example .env
# 编辑 .env，填入真实 Secret（不得提交 .env）

# 安装依赖（后续补 requirements.txt）
pip install fastapi uvicorn

# 启动服务（骨架阶段）
uvicorn src.main:app --host 0.0.0.0 --port 8101
```

## API 端点（骨架阶段）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /health | 健康检查 |
| GET | /api/v1/status | 服务状态 |
| GET | /api/v1/positions | 持仓查询（占位） |
| GET | /api/v1/orders | 订单查询（占位） |
| POST | /api/v1/orders | 下单（占位） |

## 批次进度

- ✅ A0：`.env.example` 占位符字段冻结（commit e713640）
- ✅ A1：入口 + API 骨架（本批次）
- ⏳ B：execution / ledger 骨架
- ⏳ C：risk / gateway 骨架 + 风控钩子占位
