# TASK-0005 backtest 容器命名交接单

【签名】项目架构师
【时间】2026-04-04
【设备】MacBook

## 任务结论

- TASK-0005 已完成预审建档。
- 本轮目标冻结为：在 `services/backtest/docker-compose.yml` 内统一 backtest 容器命名为 `JBT-BACKTEST-端口` 全大写格式。
- 当前公共状态应补充为：**TASK-0005 backtest 容器命名统一已预审，待 Jay.S 对单文件 P1 Token 作本轮即时执行确认。**

## 只读复核摘要

1. `services/backtest/docker-compose.yml` 当前 `container_name` 为 `backtest-api` 与 `backtest-dashboard`，尚未统一到 JBT 全大写命名规范。
2. 当前端口绑定已固定为 `8103` 与 `3001`，可直接支撑按端口冻结命名。
3. `image`、`environment`、`depends_on`、`healthcheck`、网络与卷配置本轮都不是阻塞项，无需纳入修改范围。
4. 当前运行中的临时 API 容器 `botquant-backtest-api:8004` 可作为执行态例外更名为 `JBT-BACKTEST-8004`，但不进入仓内业务白名单。
5. 本轮不涉及 contracts、不涉及其他服务、不涉及前端页面文件。

## 冻结白名单

### P1 业务文件

1. `services/backtest/docker-compose.yml`

### 本轮不纳入白名单

1. `docker-compose.dev.yml`
2. `services/backtest/Dockerfile`
3. `services/backtest/backtest_web/**`
4. `services/backtest/.env.example`
5. `services/backtest/src/**`
6. `services/backtest/tests/**`
7. `shared/contracts/**`
8. 其他全部非白名单文件

## 命名规范冻结

1. API 容器：`JBT-BACKTEST-8103`
2. Dashboard 容器：`JBT-BACKTEST-3001`
3. 运行态临时 API 容器例外：`JBT-BACKTEST-8004`（仅运行态，不进入仓内白名单）

## 执行 Agent 建议

- 默认建议：**回测 Agent**。
- 原因：唯一业务白名单文件位于 `services/backtest/`，且运行态 `8004` 例外如需处理也属于回测服务执行上下文。

## 是否可以直接申请 Token

- 可以。
- 建议申请：**单 Agent、单任务、单文件的 P1 Token。**
- 当前会话口径可记录为：**待本轮即时执行确认。**

## 向 Jay.S 汇报摘要

1. 已新建 TASK-0005 的 task / review / lock / rollback / handoff 全套治理文件。
2. 最小业务白名单已严格冻结为单文件：`services/backtest/docker-compose.yml`。
3. 命名结论已冻结为 `JBT-BACKTEST-8103` 与 `JBT-BACKTEST-3001`。
4. 运行态临时 API 容器 `8004` 仅保留为执行侧例外，不进入仓内业务白名单。

## 下一步建议

1. 由 Jay.S 为 `services/backtest/docker-compose.yml` 签发单文件 P1 Token。
2. 回测 Agent 仅在白名单范围内修改 Compose 中的容器命名字段。
3. 完成自校验与 handoff 后，再回交项目架构师终审。