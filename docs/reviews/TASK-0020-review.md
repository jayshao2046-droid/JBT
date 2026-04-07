# TASK-0020 Review

## Review 信息

- 任务 ID：TASK-0020
- 审核角色：项目架构师
- 审核阶段：sim-trading ECS 云部署与 JBotQuant.com 域名接入预审
- 审核时间：2026-04-07
- 审核结论：通过（当前轮次已冻结 ECS MVP 拓扑、域名入口、Nginx 反代与后续仓内热修边界；本轮白名单仅限治理账本与 prompt，不进入 `services/**`、`docker-compose.dev.yml` 或任何 ECS 运维执行）

---

## 一、任务目标

1. 冻结 sim-trading 第一阶段 ECS 上线与 JBotQuant.com 域名接入的最小拓扑。
2. 冻结公网入口、Nginx 反代与根域跳转口径。
3. 冻结当前基础设施准入阻塞与后续仓内热修的最小候选范围。

## 二、当前轮次白名单

1. `docs/tasks/TASK-0020-sim-trading-ECS云部署与域名接入预审.md`
2. `docs/reviews/TASK-0020-review.md`
3. `docs/locks/TASK-0020-lock.md`
4. `docs/prompts/公共项目提示词.md`
5. `docs/prompts/agents/项目架构师提示词.md`

## 三、当前轮次代码 Token 策略

1. 当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。
2. 若后续进入仓内热修，`docker-compose.dev.yml` 需要单文件 P0 Token。
3. 若后续确认前端反代或镜像构建存在仓内问题，`services/sim-trading/sim-trading_web/next.config.mjs` 与 `services/sim-trading/sim-trading_web/Dockerfile` 需要条件性 P1 Token。
4. `services/**`、`shared/contracts/**` 与其他非白名单文件当前均不解锁。

## 四、正式冻结结论

1. `TASK-0020` 必须独立建档，不复用 `TASK-0017`。
2. MVP 只允许单台 ECS，仅部署 `sim-trading` 与 `sim-trading-web` 两容器。
3. 对外业务入口只允许 `80/443`；Nginx 同域反代冻结为 `/` -> `3002`、`/api/sim/` -> `8101`。
4. `sim.jbotquant.com` 为第一阶段唯一正式业务入口；`jbotquant.com` 与 `www.jbotquant.com` 第一阶段只做跳转到 `sim.jbotquant.com`，不承载正式业务页面。
5. 首轮优先走运维路径；若 ECS Linux 兼容性暴露仓内问题，再单独补签 `docker-compose.dev.yml` 的 P0 热修票。
6. 条件性 P1 文件只允许优先评估 `services/sim-trading/sim-trading_web/next.config.mjs` 与 `services/sim-trading/sim-trading_web/Dockerfile`。
7. 当前状态冻结为“预审已建档，但被基础设施准入阻塞”；阻塞明确为 **DNS 未解析 + ECS SSH 凭证未就绪**。

## 五、当前轮次通过标准

1. 已把 ECS 云部署与域名接入独立为 `TASK-0020`。
2. 已明确 MVP 只上线 `sim-trading` 与 `sim-trading-web`，不扩展其他服务。
3. 已明确 `sim.jbotquant.com`、根域 / www 跳转策略与 Nginx 反代口径。
4. 已明确本轮只做 P-LOG，不申请代码 Token，不触碰服务代码。
5. 已明确后续仓内热修的 P0 / 条件性 P1 候选文件，以及当前继续锁定范围。

## 六、当前轮次未进入代码执行的原因

1. 当前三条域名 `jbotquant.com`、`www.jbotquant.com`、`sim.jbotquant.com` 均未解析。
2. 目标 ECS 现阶段缺少可用 SSH 登录凭证；`root`、`ecs-user`、`ubuntu`、`admin`、`centos` 探测均返回 `Permission denied`。
3. 本轮冻结路径明确为“先基础设施准入，后判断是否需要仓内热修”，因此不先行申请任何 P0 / P1 Token。
4. 当前未具备 ECS 登录条件，无法合法进入运维执行或验证仓内补丁是否必要。

## 七、预审结论

1. **`TASK-0020` 预审通过。**
2. **当前轮次只完成 ECS 云部署与域名接入治理冻结，不进入代码执行。**
3. **后续进入实施前，必须先解除 DNS 未解析与 ECS SSH 凭证未就绪两项基础设施准入阻塞。**
4. **若后续确需仓内热修，必须重新补充预审，并按 `docker-compose.dev.yml` P0 优先、`next.config.mjs` / `Dockerfile` 条件性 P1 的顺序签发 Token。**