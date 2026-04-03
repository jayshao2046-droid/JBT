# JBT Workspace

JBT 是 BotQuant 的下一代多服务工作区。

目标不是在一个大仓库里继续修补，而是把系统拆成边界清晰、目录独立、API 互通的多个服务目录。每个子目录未来对应一个独立容器，由 MacBook 作为唯一开发母仓，完成开发后同步到 Studio / Mini 等远端运行端。

## 工作区目标

1. 保持现有业务逻辑不变，但重构服务边界。
2. 将模拟交易端、实盘交易端、回测端、决策端、数据端、看板端完全拆分。
3. 每个端只保留自己的配置、日志、账本、通知与数据。
4. 任何跨服务数据交换都通过 API 与契约文件完成。
5. 与当前正在运营的 J_BotQuant 通过兼容适配层对接，不直接耦合代码。

## 技术基线

- Python 3.9
- FastAPI
- Pydantic v2
- APScheduler
- httpx
- DuckDB + Polars + PyArrow
- pytest
- Docker / Docker Compose
- Feishu Webhook / 通知链

## 目录结构

```text
jbt/
  docs/
  services/
    sim-trading/
    live-trading/
    backtest/
    decision/
    data/
    dashboard/
  shared/
    contracts/
    python-common/
    observability/
  integrations/
    legacy-botquant/
  .github/
    agents/
    instructions/
    copilot-instructions.md
```

## 根规则

1. 不允许跨服务直接读取对方目录中的账本、日志、配置或运行数据。
2. 不允许跨服务互相 import 业务代码。
3. 公共模型只进入 `shared/contracts`，公共无状态工具只进入 `shared/python-common`。
4. 所有通知链必须按服务拆分，禁止复用“全项目共用 webhook”作为默认行为。
5. 现网 J_BotQuant 只通过 `integrations/legacy-botquant` 对接，不直接复制旧交易模块。

## 当前文档入口

- `WORKFLOW.md`
- `docs/自动化迁移开发部署工作流.md`
- `docs/独立提交与回滚策略.md`
- `docs/prompts/总项目经理调度提示词.md`
- `docs/prompts/公共项目提示词.md`
- `docs/JBT_MASTER_PLAN.md`
- `docs/ARCHITECTURE_BOUNDARIES.md`
- `docs/PORT_REGISTRY.md`
- `docs/MULTI_AGENT_COLLABORATION.md`
