# TASK-0020 Lock 记录

## Lock 信息

- 任务 ID：TASK-0020
- 阶段：sim-trading ECS 云部署与 JBotQuant.com 域名接入预审
- 当前任务是否仍处于“预审未执行”状态：整体是；预审已建档，但被基础设施准入阻塞
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - Jay.S / 指定运维角色（后续 ECS 准入与部署动作）
  - 模拟交易 Agent（如后续触发仓内热修）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - 后续仓内热修 P0 首选：`docker-compose.dev.yml`
  - 后续条件性 P1 文件：`services/sim-trading/sim-trading_web/next.config.mjs`、`services/sim-trading/sim-trading_web/Dockerfile`

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0020-sim-trading-ECS云部署与域名接入预审.md`
2. `docs/reviews/TASK-0020-review.md`
3. `docs/locks/TASK-0020-lock.md`
4. `docs/prompts/公共项目提示词.md`
5. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `services/**`
2. `docker-compose.dev.yml`
3. `shared/contracts/**`
4. 其他全部非白名单文件

## 基础设施准入阻塞

1. `jbotquant.com`、`www.jbotquant.com`、`sim.jbotquant.com` 当前均未解析到有效 A 记录。
2. 目标 ECS 当前公开探测 IP 为 `47.103.36.144`。
3. `root`、`ecs-user`、`ubuntu`、`admin`、`centos` 的 SSH 探测均返回 `Permission denied`，可视为 SSH 凭证未就绪。
4. 当前阻塞冻结为：**DNS 未解析 + ECS SSH 凭证未就绪。**

## 后续仓内热修候选文件（仅条件触发）

### P0 首选

1. 文件：`docker-compose.dev.yml`
2. 触发条件：ECS Linux 兼容性、Compose 编排或容器启动路径证明必须通过仓内编排热修才能闭环。
3. 当前 Token 状态：未申请；仅在补充预审后可转为 pending_token。

### 条件性 P1 文件

1. 文件：`services/sim-trading/sim-trading_web/next.config.mjs`
2. 触发条件：同域反代、域名入口或 Next.js 代理行为在 ECS 上暴露仓内问题。
3. 当前 Token 状态：未申请；仅在补充预审后可转为 pending_token。

4. 文件：`services/sim-trading/sim-trading_web/Dockerfile`
5. 触发条件：镜像构建、运行时依赖或 ECS Linux 基础镜像行为暴露仓内问题。
6. 当前 Token 状态：未申请；仅在补充预审后可转为 pending_token。

## 当前继续禁止修改的路径说明

1. 当前 `services/**` 仍未对本任务解锁，禁止写入。
2. 当前 `docker-compose.dev.yml` 仍继续锁定，禁止以“提前热修”名义写入。
3. 当前 `shared/contracts/**` 与其他全部非白名单文件继续锁定。
4. 禁止把 `TASK-0020` 与 `TASK-0017` 混批执行。
5. 禁止在 DNS 与 SSH 未就绪的情况下预先宣称 ECS 可上线或需要仓内补丁。

## 进入执行前需要的 Token / 授权

1. 必须先完成 `jbotquant.com`、`www.jbotquant.com`、`sim.jbotquant.com` 的有效解析。
2. 必须先由 Jay.S 提供目标 ECS 的有效 SSH 登录用户名与凭证。
3. 若基础设施准入后确认需要仓内热修，必须先补充预审，再按文件级白名单申请 P0 / P1 Token。
4. 若不需要仓内热修，则继续走运维路径，不得把运维动作伪装成代码任务。

## 当前状态

- 预审状态：已通过
- Token 状态：当前轮次未申请代码 Token
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行阶段

## 结论

**`TASK-0020` 当前仍处于“预审已建档，但被基础设施准入阻塞”状态；继续锁定 `services/**`、`docker-compose.dev.yml`、`shared/contracts/**` 及其他非白名单文件。**