# TASK-0020 sim-trading ECS 云部署与 JBotQuant.com 域名接入预审

## 文档信息

- 任务 ID：TASK-0020
- 文档类型：新任务预审与边界冻结
- 签名：项目架构师
- 建档时间：2026-04-07
- 设备：MacBook

---

## 一、任务目标

为 sim-trading 主线建立独立的“ECS 云部署与 JBotQuant.com 域名接入”任务，冻结 MVP 部署拓扑、域名入口、Nginx 反代、公网暴露口径与后续仓内热修边界。

本任务当前轮次只做预审建档，不写任何服务代码，不进入任何 ECS 运维执行。

---

## 二、任务编号与归属结论

### 编号结论

- **sim-trading ECS 云部署与域名接入必须新建独立任务 `TASK-0020`，不得复用 `TASK-0017`。**

### 判定理由

1. `TASK-0017` 收口的是 Docker 化与 Mini 部署治理，不承接 ECS 云主机、域名解析、Nginx 入口与公网接入。
2. ECS + DNS + Nginx + 根域跳转属于独立的基础设施准入问题，验收口径与 Mini 部署不同。
3. 若复用 `TASK-0017`，会把 Mini 运维验证与 ECS 上线接入混成同一任务，违反“一件事一审核一上锁”。

### 服务归属结论

- **MVP 业务归属继续冻结为 `services/sim-trading/**` 单服务上线。**
- **首轮容器范围只允许 `sim-trading` 与 `sim-trading-web` 两个容器。**
- **根域名、www、sim 子域名解析、Nginx 与 ECS 登录属于基础设施准入事项，不构成新的服务代码归属。**

### 执行 Agent

1. 预审：项目架构师
2. 后续基础设施准入与部署：Jay.S / 指定运维角色
3. 后续仓内热修：模拟交易 Agent（仅在补充预审 + Token 后）

---

## 三、当前轮次白名单与保护级别

### 当前 Git 白名单

1. `docs/tasks/TASK-0020-sim-trading-ECS云部署与域名接入预审.md`
2. `docs/reviews/TASK-0020-review.md`
3. `docs/locks/TASK-0020-lock.md`
4. `docs/prompts/公共项目提示词.md`
5. `docs/prompts/agents/项目架构师提示词.md`

### 当前保护级别

- **当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。**

### 当前轮次明确禁止

1. 不得修改 `services/**`。
2. 不得修改 `docker-compose.dev.yml`。
3. 不得修改 `shared/contracts/**`。
4. 不得修改其他全部非白名单文件。
5. 不得在未获得 ECS 凭证前假定远端 OS、Docker、Nginx 或证书路径可直接复用。

---

## 四、已知只读事实与当前阻塞

1. `jbotquant.com`、`www.jbotquant.com`、`sim.jbotquant.com` 当前均未解析到任何 A 记录。
2. 目标 ECS 当前公开探测 IP 为 `47.103.36.144`。
3. `root`、`ecs-user`、`ubuntu`、`admin`、`centos` 账户的 SSH 只读登录探测均返回 `Permission denied`。
4. 当前任务状态不是“执行中”，而是“预审已建档，但被基础设施准入阻塞”。
5. 当前阻塞冻结为：**DNS 未解析 + ECS SSH 凭证未就绪。**

---

## 五、前置依赖

1. 为 `jbotquant.com`、`www.jbotquant.com`、`sim.jbotquant.com` 准备有效解析记录。
2. 为目标 ECS 提供可用 SSH 登录凭证与登录用户名。
3. 仅在 ECS 登录可用后，才允许验证 OS、Docker、Nginx 与证书路径是否需要仓内补丁。

---

## 六、正式治理冻结

### 1. MVP 部署拓扑

1. **MVP 只允许单台 ECS。**
2. **只部署 `sim-trading` 与 `sim-trading-web` 两个容器。**
3. 除 Nginx 入口外，不新增 `dashboard`、`decision`、`data`、`live-trading` 容器。

### 2. 公网入口与反代口径

1. **对外业务端口只允许 `80` / `443`。**
2. **Nginx 同域反代冻结为：**
   - `/` -> `3002`
   - `/api/sim/` -> `8101`
3. 内部容器端口语义继续保持 `sim-trading-web=3002`、`sim-trading=8101`，不得为公网入口改写服务端口语义。
4. SSH 登录与运维通道不纳入“业务对外开放端口”口径，由运维单独控制。

### 3. 域名入口策略

1. **`sim.jbotquant.com` 为第一阶段唯一正式业务入口。**
2. **`jbotquant.com` 与 `www.jbotquant.com` 第一阶段只做跳转到 `sim.jbotquant.com`。**
3. 第一阶段根域与 www 不承载正式业务页面。

### 4. 执行路径结论

1. **首轮优先走运维路径，不先申请仓内代码 Token。**
2. 只有在 ECS Linux 兼容性、Compose 编排或前端反代行为暴露仓内问题时，才允许补签仓内热修票。
3. 若后续确认需要仓内热修，**P0 首选文件为 `docker-compose.dev.yml`。**
4. 条件性 P1 文件只允许优先评估：
   - `services/sim-trading/sim-trading_web/next.config.mjs`
   - `services/sim-trading/sim-trading_web/Dockerfile`
5. 在未补充预审前，不得预先解锁上述文件。

---

## 七、Token / 保护级别策略

1. 当前轮次：P-LOG，仅治理账本，不申请代码 Token。
2. 后续若进入 ECS 兼容性热修：`docker-compose.dev.yml` 按 **P0** 单文件处理。
3. 后续若前端域名反代或镜像构建确有仓内问题：`services/sim-trading/sim-trading_web/next.config.mjs` 与 `services/sim-trading/sim-trading_web/Dockerfile` 按条件性 **P1** 单文件或最小白名单处理。
4. 任何新增白名单都必须重新预审，不得沿用本轮 P-LOG 白名单。

---

## 八、验收标准

1. 已把 ECS 云部署与域名接入从 `TASK-0017` 中独立拆出为 `TASK-0020`。
2. 已冻结 MVP 为单 ECS + 两容器 + `sim.jbotquant.com` 入口。
3. 已冻结对外仅 `80/443`、Nginx 反代 `/` -> `3002` 与 `/api/sim/` -> `8101`。
4. 已冻结根域与 www 第一阶段只做跳转，不承载正式业务页面。
5. 已明确当前阻塞为 **DNS 未解析 + ECS SSH 凭证未就绪**。
6. 已明确本轮只做 P-LOG，不申请代码 Token，不触碰任何服务代码。

---

## 九、预审结论

1. **`TASK-0020` 正式成立。**
2. **`TASK-0020` 必须独立于 `TASK-0017`，因为它属于 ECS 基础设施准入与域名接入，而不是 Mini 部署延续。**
3. **MVP 部署口径冻结为：单台 ECS、`sim-trading` + `sim-trading-web` 两容器、对外仅 `80/443`、Nginx 同域反代 `/` -> `3002`、`/api/sim/` -> `8101`、`sim.jbotquant.com` 为唯一正式业务入口。**
4. **`jbotquant.com` 与 `www.jbotquant.com` 第一阶段只跳转到 `sim.jbotquant.com`，不承载正式业务页面。**
5. **当前状态冻结为“预审已建档，但被基础设施准入阻塞”；当前阻塞为 DNS 未解析 + ECS SSH 凭证未就绪。**
6. **当前轮次仅完成治理冻结，不进入代码 Token 申请，不进入任何服务代码或 ECS 运维执行。**