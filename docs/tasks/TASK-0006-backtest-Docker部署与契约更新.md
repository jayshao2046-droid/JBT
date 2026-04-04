# TASK-0006 — backtest Docker 部署与契约更新

## 任务信息

- 任务 ID：TASK-0006
- 创建时间：2026-04-04
- 预审角色：项目架构师
- 预审结论：**通过**
- 状态：已预审，白名单已冻结，待 Jay.S 签发 Token

## 任务背景

Jay.S 要求完成回测端最后三件事，其中 Git commit（afa635b）已完成。本任务处理剩余两项：

1. Docker 配置 + 远端部署（目标 192.168.31.245，用户 jayshao，内网优先）
2. `shared/contracts/backtest/api.md` 更新：补充通用模板支持说明

## 任务目标

1. 新建 `services/backtest/Dockerfile` — backtest FastAPI 后端 Docker 镜像（Python 3.11，uvicorn，端口 8103）
2. 新建 `services/backtest/V0-backtext 看板/Dockerfile` — Next.js 看板 Docker 镜像（pnpm + next start，端口 3001）
3. 新建 `services/backtest/docker-compose.yml` — 组合编排文件，包含 backtest-api + backtest-dashboard 两个容器，均设置 `restart: always`（确保常驻）
4. 修改 `shared/contracts/backtest/api.md` — 在"当前任务输入口径"节追加通用模板支持说明（`strategy_template_id` 现在支持 FC-224 和任意通用模板 ID，不再仅限 `fc_224_strategy`）
5. 将上述 Docker 配置推送到 192.168.31.245（jayshao）并在远端完成 `docker-compose up -d` 部署

## 白名单（共 4 文件）

| # | 文件路径 | 操作 | 保护级别 | 备注 |
|---|---|---|---|---|
| 1 | `services/backtest/Dockerfile` | 新建 | P1 | 不在 P0 保护路径 |
| 2 | `services/backtest/V0-backtext 看板/Dockerfile` | 新建 | P1 | 不在 P0 保护路径 |
| 3 | `services/backtest/docker-compose.yml` | 新建 | P1 | 不在 P0 保护路径 |
| 4 | `shared/contracts/backtest/api.md` | 修改 | **P0** | `shared/contracts/**` 保护区，需 P0 Token |

共 4 文件，在 WORKFLOW 5 文件上限内。

## 边界约束

1. 不修改 `docker-compose.dev.yml`（根目录，P0）
2. 不修改 `services/backtest/.env.example`（P0）
3. backtest Dockerfile 必须从 `.env.example` 标注的环境变量读取配置，不硬编码任何凭证
4. 看板 Dockerfile 不需要 TqSdk 凭证，仅做前端静态构建 + next start
5. 不修改其他 `shared/contracts/**` 文件（仅允许改 `api.md` 的"当前任务输入口径"节）
6. 不触碰任何已锁回的 `services/backtest/src/backtest/**` 业务文件

## Token 要求

| Token 类型 | 文件范围 | 备注 |
|---|---|---|
| P1 Token | 文件 #1、#2、#3 | 三个新建文件，位于 P1 区 |
| P0 Token | 文件 #4 | `shared/contracts/**` 保护区，需单独 P0 Token |

**注意**：Jay.S 要求完成此工作视为已授权，但仍需走标准 Token 签发流程。建议分两枚 Token 签发（P1 + P0），也可合并为一枚多文件 Token（需 Jay.S 确认范围）。

## 远端部署约束

- 目标主机：192.168.31.245（Air，jayshao）
- 连接方式：内网 SSH
- 部署命令：`docker-compose up -d`（在 `services/backtest/` 对应目录执行）
- backtest-api 端口：8103
- backtest-dashboard 端口：3001
- 两个容器均需设置 `restart: always`

## 验收标准

1. `services/backtest/Dockerfile` 可在目标机器上成功 `docker build`，不含硬编码凭证
2. `services/backtest/V0-backtext 看板/Dockerfile` 可在目标机器上成功 `docker build`
3. `services/backtest/docker-compose.yml` 中 backtest-api 与 backtest-dashboard 均可 `docker-compose up -d` 正常启动
4. 远端 192.168.31.245 上两个容器 `docker ps` 状态为 `Up` 且端口 8103 / 3001 可响应
5. `shared/contracts/backtest/api.md` 的"当前任务输入口径"节包含以下说明：`strategy_template_id` 现在支持 FC-224 和任意通用模板 ID，不再仅限 `fc_224_strategy`；整体格式与现有契约保持一致
