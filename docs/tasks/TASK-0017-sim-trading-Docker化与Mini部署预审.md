# TASK-0017 sim-trading Docker 化与 Mini 部署预审

## 文档信息

- 任务 ID：TASK-0017
- 文档类型：新任务预审与部署边界冻结
- 签名：项目架构师
- 建档时间：2026-04-06
- 设备：MacBook

---

## 一、任务目标

把“Docker 化并远端 Mini 部署”的事项独立建档，冻结其与服务实现、legacy 清退和运行时 Secret 的边界。

本任务当前轮次只做预审，不写任何 Docker、compose 或远端运维文件。

---

## 二、任务编号与归属结论

### 编号结论

- **F Docker 化与 Mini 部署必须新建独立任务 `TASK-0017`。**

### 判定理由

1. Docker 化与远端部署同时涉及仓内文件、运行时 Secret、Mini 环境验证与回滚方案，不能混入 `TASK-0010` 服务骨架。
2. 该事项也不等于 `TASK-0011` legacy tqsim 清退；部署成功不代表可以顺手清理 legacy。
3. 若混并，会把代码构建、远端部署、切换验证与运维回滚混成一件事，违反“一件事一审核一上锁”。

### 归属结论

- **当前轮次归属：跨治理层部署任务。**
- **未来实施可能同时涉及 `services/sim-trading/**`、`services/dashboard/**`、`docker-compose.dev.yml` 与远端 Mini 运维动作，但必须按保护级别拆批。**

### 执行 Agent

1. 预审：项目架构师
2. 未来仓内实现：对应服务 Agent
3. 未来远端部署执行：Atlas（仅在 Jay.S 明确逐条授权后）

---

## 三、当前轮次白名单与保护级别

### 当前 Git 白名单

1. `docs/tasks/TASK-0017-sim-trading-Docker化与Mini部署预审.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/项目架构师提示词.md`

### 当前保护级别

- **当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。**

### 当前轮次明确禁止

1. 不得修改 `services/sim-trading/**`。
2. 不得修改 `services/dashboard/**`。
3. 不得修改 `docker-compose.dev.yml`。
4. 不得执行任何远端 Mini 部署、容器启停或 Secret 写入动作。
5. 不得把本任务与 `TASK-0011` legacy 清退混并。

---

## 四、前置依赖

1. `TASK-0009` 已闭环。
2. `TASK-0013` 已冻结统一风控核心与阶段预设口径。
3. `TASK-0010` 已完成最小服务骨架并通过本地最小验证。
4. `TASK-0014` 已完成最小通知链路验证。
5. `TASK-0015` 的临时看板路径与只读 API 已明确，或 Jay.S 已书面豁免其为部署前置。
6. `TASK-0016` 的正式接入测试结论已明确。
7. Jay.S 已批准进入 Mini 部署验证窗口。

---

## 五、正式治理冻结

### 1. 与 `TASK-0011` 的边界

1. `TASK-0017` 负责 Docker 化、Mini 部署与切换前验证。
2. `TASK-0011` 负责 legacy tqsim 清退。
3. **部署完成不等于允许清退 legacy；清退仍需单独满足 `TASK-0011` 前置条件。**

### 2. 未来实施拆批原则

1. 若新增 / 修改 `services/sim-trading/**` 或 `services/dashboard/**` 下的 Dockerfile、启动脚本等服务文件：按各自服务 **P1** 批次处理。
2. 若新增 / 修改 `docker-compose.dev.yml`：单独 **P0** 批次处理。
3. 若新增 / 修改各服务 `.env.example`：单独 **P0** 批次处理。
4. 远端 Mini 的容器启动、Secret 注入、镜像切换、回滚验证不属于 Git Token，本质上属于运维动作，必须由 Atlas 在 Jay.S 明确授权后逐条执行。

### 3. 部署验收范围

1. Mini 上必须先完成镜像构建与容器启动验证，再谈切换。
2. 切换前必须验证：健康检查、只减仓、最小通知、上游接入路径、回滚路径，以及断网 / 断数据源下的本地缓存行为。
3. “断网 / 断数据源下的本地缓存行为验证”属于系统级风控执行验证细节，不构成新增规则；验证通过标准为：Studio 侧 L1 / L2 决策在 Mini 断网或上游数据源中断时，要么正确读取最近一次本地快照继续做安全降级判断，要么正确拒绝开仓并进入 Fail-Safe。
4. 上述验证路径下，系统绝不能 crash，也不能生成错误交易信号。
5. 任何 Secret 只允许在运行时注入，不允许烘焙进镜像、compose、仓库文件或治理账本。

---

## 六、Token / 保护级别策略

1. 当前轮次：P-LOG，仅治理账本，不申请代码 Token。
2. 未来若修改 `services/sim-trading/**` 或 `services/dashboard/**` 服务内 Docker 相关文件：**P1**。
3. 未来若修改 `docker-compose.dev.yml`：**P0**。
4. 未来若修改各服务 `.env.example`：**P0**。
5. 远端 Mini 运维动作：**不适用 Git Token**，但必须有 Jay.S 明确运维授权。

---

## 七、敏感信息治理

1. SimNow 账号密码、通知凭证、API 密钥、Mini 运行时 Secret 只能在远端运行时注入，不得写入 Git、镜像、`.env.example` 或治理账本。
2. compose 与 Dockerfile 只能保留占位符、字段说明与 Secret 挂载方式，不能写真实值。
3. 任何来自 J_BotQuant 的配置方案只能写“来源”“接入方式”“注入位置”，不得写明文秘密值。

---

## 八、验收标准

1. 已冻结 `TASK-0017` 与 `TASK-0011` 的边界。
2. 已冻结未来 Docker / compose / `.env.example` / 远端运维的保护级别划分。
3. 已明确 Mini 部署前必须验证的最小检查项，其中包含“断网 / 断数据源下的本地缓存行为验证”，且该项被定义为系统级风控执行细节而非新增规则。
4. 已明确本任务在补充文件级白名单与远端执行授权前，不进入代码 Token 或运维执行。

---

## 九、预审结论

1. **`TASK-0017` 正式成立。**
2. **F Docker 化与 Mini 部署必须作为独立部署任务推进，不得与 `TASK-0011` legacy 清退混并。**
3. **在文件级白名单与 Mini 运维授权补齐前，本任务暂不进入代码 Token 或远端执行。**