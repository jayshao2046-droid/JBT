# JBT 治理规则 — Claude Code

## 开工必读

每次开始重大修改前，先读取以下文件：

1. `ATLAS_PROMPT.md` — Atlas 当前状态与待办
2. `docs/plans/ATLAS_MASTER_PLAN.md` — 项目总计划
3. `PROJECT_CONTEXT.md` — 项目上下文与接管规则
4. `docs/prompts/总项目经理调度提示词.md` — 总项目经理调度
5. `docs/prompts/公共项目提示词.md` — 公共项目规则

## 权威来源

- JBT 是唯一的活跃开发工作区；J_BotQuant 为 legacy，只读。
- 不得从 J_BotQuant 复制业务逻辑到 JBT 服务下，兼容逻辑只允许放在 `integrations/legacy-botquant/`。
- 不得创建第二套业务 prompt 体系；业务含义来源唯一：`ATLAS_PROMPT.md` 和 `docs/prompts/`。

## 写操作前置门禁

在对任意文件执行写操作前，**必须**验证以下所有条件：

1. 当前任务已在 `docs/tasks/` 登记。
2. 项目架构师已完成预审（`docs/reviews/` 有对应记录）。
3. 目标文件在当前任务的文件级白名单中。
4. Jay.S 已为这些文件签发有效 Token（通过 `jbt-governance` MCP 工具中的 `check_token_access` 验证）。

**验证方式**：调用 `check_token_access` 工具，传入 `task_id`、`agent`、`action` 和 `files` 列表。如果返回 `allowed: false`，必须停止写操作并向 Atlas 汇报。

## 只读检查规则

- 只读诊断（读文件、搜索、漏洞发现）在写操作门禁前是允许的。
- 一旦确认需要写操作，立即停止，向 Atlas 汇报最小文件范围、服务边界和验收计划。
- 不得将只读检查顺手转为实现批次。

## Mini 数据节点只读规则（永久硬约束，2026-04-23 Jay.S 确认）

**Mini（192.168.31.74）上的 `services/data/` 目录及相关文件属于永久禁改区，适用以下约束：**

1. **即使在 U0 直修模式下，无 Token 也不得修改 Mini data 服务的任何文件。**
2. **禁止通过 rsync / scp / ssh 直写 Mini 上的任何 `services/data/**` 文件。**
3. **所有对 Mini 数据的读取和查询，必须通过 API 接入（`http://192.168.31.74:8105`），不得直接操作 Mini 文件系统。**
4. **本规则不因任何模式（V2 / U0 / 标准流程）而豁免；U0 的"单服务无 Token 直修"权限不覆盖 Mini data 服务。**
5. **若 Mini data 服务确需修改，必须在 MacBook 本地 `services/data/` 完成开发、通过标准流程签发 Token 后，再通过 rsync 同步并 docker restart 验证，且每次同步须留 handoff 记录。**

> 背景：Mini 是四设备中唯一的数据采集节点，24/7 运行，任何未经审计的直接修改均存在破坏数据管道的高风险。API 接入是唯一授权的只读访问通道。

## 保护路径（禁止未授权写入）

以下路径未经明确 Token 授权不得触碰：

- `services/**`（所有服务代码）
- `shared/contracts/**`
- `shared/python-common/**`
- `integrations/**`
- `WORKFLOW.md`
- `.github/**`
- `docker-compose.dev.yml`
- `services/*/.env.example`
- `runtime/**`、`logs/**`、任何真实 `.env` 文件
- `governance/jbt_lockctl.py`

## 协同账本路径（免 Token，但有角色限制）

以下路径不需要代码 Token，但有角色独占写权限：

| 路径 | 可写角色 |
|------|---------|
| `docs/tasks/**` | Atlas |
| `docs/reviews/**` | 项目架构师 |
| `docs/locks/**` | Atlas（锁控记录） |
| `docs/handoffs/**` | 任意 Agent |
| `docs/prompts/总项目经理调度提示词.md` | 仅 Atlas |
| `docs/prompts/公共项目提示词.md` | 仅项目架构师 |
| `docs/prompts/agents/**` | 对应 Agent 私有 |

## 批次收口流程

每个批次完成后：

1. 调用 `append_atlas_log` 工具将批次摘要写入 `ATLAS_PROMPT.md`（签名：所执行 Agent 名称）。
2. 停止，等待 Atlas 复审。
3. Atlas 确认 → 项目架构师终审 → 锁回 → 独立 commit → 同步到 Mini/Studio。
4. 摘要使用中文，内容具体到可审计粒度。

## 服务归属

- `services/sim-trading/`：模拟交易、账本、执行风控
- `services/live-trading/`：实盘交易
- `services/backtest/`：历史回测与参数优化
- `services/decision/`：因子、信号、审批编排
- `services/data/`：数据采集、标准化、供数
- `services/dashboard/`：看板与只读聚合

不同服务之间除 `shared/contracts` 与 `shared/python-common` 外，禁止跨服务 import。

## MCP 工具使用

通过 `jbt-governance` MCP Server 提供三个工具：

- `workflow_status` — 查询当前活跃 token、启动链与治理规则摘要
- `check_token_access` — 验证指定文件的 token 是否有效（写操作前必须调用）
- `append_atlas_log` — 向 ATLAS_PROMPT.md 追加批次日志（仅当 ATLAS_PROMPT.md 在白名单中时有效）

## 四设备连接规范（2026-04-20 Jay.S 确认，唯一权威来源）

> 禁止使用下表以外的 IP、用户名或端口连接任何设备。内网默认直连本地 IP；外网优先蒲公英，次选 Tailscale。

| 设备 | 角色 | 内网 IP | Tailscale | 蒲公英 | SSH 用户 | 主要服务 |
|------|------|---------|-----------|--------|---------|--------|
| **Mini** | 数据采集节点 | 192.168.31.74 | 100.83.139.52 | 172.16.0.49 | jaybot | data:8105, data-web:3004 |
| **Alienware** | 交易执行 + 研究员节点 | 192.168.31.187 | 100.91.19.67 | — | 17621 | sim-trading:8101, researcher:8199 |
| **Studio** | 决策/看板/回测主控 | 192.168.31.142 | 100.86.182.114 | 172.16.1.130 | jaybot | decision:8104, backtest:8103, dashboard:8106/3005 |
| **Air** | 回测生产节点 | 192.168.31.245 | 100.118.65.55 | — | jayshao | backtest:8103, backtest-web:3001 |

**SSH 快速参考**：
```bash
ssh jaybot@192.168.31.74       # Mini
ssh 17621@192.168.31.187       # Alienware
ssh jaybot@192.168.31.142      # Studio
ssh jayshao@192.168.31.245     # Air
```

**代码同步（rsync，禁止 GitHub 中转）**：
```bash
# MacBook → Mini
rsync -avz --delete /Users/jayshao/JBT/services/data/ jaybot@192.168.31.74:~/jbt/services/data/ --exclude="__pycache__" --exclude="*.pyc" --exclude=".env"
# MacBook → Studio
rsync -avz --delete /Users/jayshao/JBT/services/decision/ jaybot@192.168.31.142:~/jbt/services/decision/ --exclude="__pycache__" --exclude="*.pyc" --exclude=".env"
# MacBook → Air
rsync -avz --delete /Users/jayshao/JBT/services/backtest/ jayshao@192.168.31.245:~/jbt/services/backtest/ --exclude="__pycache__" --exclude="*.pyc" --exclude=".env"
```
