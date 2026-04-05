# TASK-0005 backtest 容器命名规范统一

## 文档信息

- 任务 ID：TASK-0005
- 文档类型：新任务预审与范围冻结
- 签名：项目架构师
- 建档时间：2026-04-04
- 设备：MacBook

---

## 一、任务目标

在 `services/backtest/` 范围内统一 backtest 容器命名规范，本轮只处理 Docker Compose 中的 `container_name` 字段，冻结 backtest 命名模板为 `JBT-BACKTEST-端口`，且必须全大写。

本轮明确目标如下：

1. API 容器命名冻结为 `JBT-BACKTEST-8103`
2. Dashboard 容器命名冻结为 `JBT-BACKTEST-3001`
3. 当前运行中的临时 API 容器 `botquant-backtest-api:8004` 可作为运行态例外更名为 `JBT-BACKTEST-8004`，但该动作不进入仓内业务白名单
4. 后续其他服务容器命名规则不在本任务内展开；本轮只在 backtest 服务内落地该规范

---

## 二、服务归属与边界判定

### 归属结论

- **任务归属：`services/backtest/` 单服务范围内的 Docker 容器命名治理。**

### 判定理由

1. 当前唯一允许改写的业务文件位于 `services/backtest/` 下。
2. 本轮只改 compose 中的容器命名字段，不涉及跨服务编排重构，也不涉及根级 `docker-compose.dev.yml`。
3. Dashboard 容器虽然承载回测看板进程，但本轮只在 backtest 服务 compose 中统一命名，不涉及任何前端页面文件。

### 强制边界

1. 本轮只允许落在 `services/backtest/docker-compose.yml`。
2. 不得扩展到 `services/backtest/backtest_web/**`、`services/backtest/Dockerfile`、`services/backtest/.env.example`、`shared/contracts/**`、`docker-compose.dev.yml`、其他服务目录。
3. 不得顺手修正端口、镜像名、环境变量、依赖关系、健康检查、网络、卷挂载等非容器命名字段。
4. 运行态容器重命名若需要执行，属于回测 Agent 的运行态操作例外，不得据此扩大仓内文件白名单。

---

## 三、只读现状结论

基于当前只读复核，得到以下结论：

1. `services/backtest/docker-compose.yml` 当前定义两个服务：`backtest-api` 与 `backtest-dashboard`。
2. 当前 `image` 字段分别为 `jbt-backtest-api:latest` 与 `jbt-backtest-dashboard:latest`，本轮无需改动 image 命名。
3. 当前 `container_name` 字段分别为 `backtest-api` 与 `backtest-dashboard`，尚未统一到 `JBT-BACKTEST-端口` 全大写规范。
4. 当前端口绑定已固定为 `8103:8103` 与 `3001:3001`，足以支撑按端口冻结容器命名，本轮无需扩展其他文件。
5. 当前运行态临时 API 容器 `botquant-backtest-api:8004` 仅作为执行态例外处理对象，不构成仓内 compose 现状的一部分，也不进入本轮业务白名单。

---

## 四、本轮最小白名单冻结

### P1 业务文件白名单

1. `services/backtest/docker-compose.yml`

### 当前明确不纳入白名单的文件

1. `docker-compose.dev.yml`
2. `services/backtest/Dockerfile`
3. `services/backtest/backtest_web/**`
4. `services/backtest/.env.example`
5. `services/backtest/src/**`
6. `services/backtest/tests/**`
7. `shared/contracts/**`
8. 其他全部非白名单文件

### 不扩白名单的理由

1. 本轮目标仅为统一 `container_name` 字段，单文件足以完成。
2. 命名冻结不需要改端口、镜像、页面代码或服务实现。
3. 运行态 `8004` 容器例外若需处理，应由执行 Agent 在运行环境完成，不应倒逼扩白名单。

---

## 五、执行 Agent 建议

### 合规默认建议

- **建议执行 Agent：回测 Agent。**

### 理由

1. 唯一业务白名单文件位于 `services/backtest/`。
2. 本轮是服务目录内 compose 命名调整，不属于项目架构师代写范围。
3. 运行态 `8004` 容器例外若执行，也应由回测 Agent 在同一服务上下文中完成。

---

## 六、Token 建议

- Token 类型：**P1 Token**
- 建议执行 Agent：**回测 Agent**
- 文件范围：**仅限 `services/backtest/docker-compose.yml`**
- 当前状态：**预审通过，待 Jay.S 对本轮即时执行作确认并签发单文件 P1 Token**

### 命名规范冻结

1. API 容器：`JBT-BACKTEST-8103`
2. Dashboard 容器：`JBT-BACKTEST-3001`

### 运行态例外

1. 当前临时 API 容器 `botquant-backtest-api:8004` 可重命名为 `JBT-BACKTEST-8004`。
2. 该动作仅属于运行态例外，不进入仓内业务文件白名单，不得据此追加 Dockerfile、脚本或其他配置文件。

---

## 七、预审结论

1. **TASK-0005 正式成立。**
2. **任务归属冻结为 `services/backtest/`。**
3. **本轮不涉及 contracts、不涉及其他服务、不涉及前端页面文件。**
4. **本轮仅允许修改 Docker Compose 中的容器命名字段。**
5. **业务白名单严格冻结为 `services/backtest/docker-compose.yml` 单文件。**
6. **命名规范已冻结为 `JBT-BACKTEST-8103` 与 `JBT-BACKTEST-3001`。**
7. **运行态临时 API 容器 `8004` 仅保留为执行侧例外口径，不计入仓内白名单。**