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

## 六、补充批次 A2 白名单扩展（2026-04-06）

### 扩展说明

在原补充批次 A2（`router.py` + `main.py`）的基础上，经项目架构师预审，追加以下两个文件进入 A2 白名单：

| 序号 | 文件路径 | 变更内容 | 保护级别 |
|------|---------|---------|---------|
| 3 | `services/sim-trading/sim-trading_web/app/intelligence/page.tsx` | 清除两处硬编码 mock 数据：「2 / 5」连续亏损计数与「60%」保证金水位改为动态 state；未接入 API 时显示「--」 | P1 |
| 4 | `docker-compose.dev.yml` | 为 sim-trading 服务添加 `platform: linux/amd64`，使 M 芯片 Mac 上的 Docker 能通过 Rosetta 2 运行 openctp-ctp | P0 |

### 变更理由

1. **`intelligence/page.tsx`**：当前页面存在两处硬编码 mock 数据（连续亏损计数 `2/5`、保证金水位 `60%`），在无后端接入时会向用户展示虚假风控状态，属于前端数据安全问题，需改为动态 state；未接入时显示「--」以明确区分"无数据"与"数据为零"。属于 `services/sim-trading/sim-trading_web/**` 范围，保护级别 P1。

2. **`docker-compose.dev.yml`**：本机为 M 芯片 Mac，openctp-ctp 目前仅提供 amd64 轮子，不加 `platform: linux/amd64` 时 Docker 默认拉 arm64 镜像导致构建失败。该字段为部署级修复，不引入任何新服务逻辑或 Secret。属于根级 compose 文件，保护级别 P0；依据本任务"五-2"拆批原则，该项本应单独 P0 批次处理——此次作为热修一并纳入 A2 扩展，但须由 Jay.S 为 `docker-compose.dev.yml` 单独签发 P0 Token，不可与 P1 Token 合并签发。

### 架构师预审结论

1. 预审通过。
2. 扩展后 A2 白名单共四个文件：`router.py`、`main.py`、`intelligence/page.tsx`（P1）、`docker-compose.dev.yml`（P0）。
3. Token 状态：pending_token — 须由 Jay.S 分别签发：① 四文件中 P1 三份按已有 A2 P1 Token 范围扩签；② `docker-compose.dev.yml` 须单独签发 P0 Token。
4. 执行 Agent：模拟交易（P1 三文件） + 项目架构师或 Atlas（P0 `docker-compose.dev.yml`，须 Jay.S 明确指定）。
5. A1 → A2 的执行顺序约束不变；`docker-compose.dev.yml` 的 P0 Token 可与 A2 P1 Token 并行签发，但 P0 文件的实施必须与 P1 三文件独立提交、独立回滚。
6. 签名：项目架构师，2026-04-06。

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
---

## 六、补充批次 A2 — 启动自动连接（startup auto-connect）

### 批次信息

- 批次名称：补充批次 A2
- 建档时间：2026-04-06
- 签名：项目架构师

### 修改目标

1. **`services/sim-trading/src/api/router.py`**：初始化 `_system_state` 时，从 `os.getenv("SIMNOW_USER_ID","")` / `os.getenv("SIMNOW_PASSWORD","")` / `os.getenv("SIMNOW_BROKER_ID","9999")` 读取值，替换目前的空字符串硬编码，使服务启动后可直接读取环境变量中的 SimNow 账号信息。

2. **`services/sim-trading/src/main.py`**：新增 `@app.on_event("startup")` async 函数，若 `SIMNOW_USER_ID` 环境变量非空，自动触发 CTP 连接逻辑，并捕获所有异常静默失败（`except Exception`），确保 CTP 连接异常不影响服务正常启动。

### 本批次白名单（A2 专属）

1. `services/sim-trading/src/api/router.py`
2. `services/sim-trading/src/main.py`

### 保护级别

- P1（服务业务代码）

### 前置约束

1. 补充批次 A1（`services/sim-trading/Dockerfile`）的 Token 签发与本地 `docker build` 自校验必须先完成，才能启动 A2 执行。
2. A2 变更范围只限上述两个文件；若执行中需要第 3 个业务文件，本批次立即失效并回交补充预审。
3. 不得在上述文件中硬编码任何 SimNow 账号、密码或真实凭证，只允许运行时 `os.getenv` 读取。
4. `docker-compose.dev.yml`、`services/sim-trading/.env.example`、`services/sim-trading/requirements.txt`、其他 `services/**` 文件与远端 Mini 运维动作均不在 A2 范围内。5. 任何 Secret 只允许在运行时注入，不允许烘焙进镜像、compose、仓库文件或治理账本。

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

## 九、补充批次 A1 冻结（2026-04-06）

### 1. 补充背景

1. 用户已明确要求继续修复 sim-trading Docker。
2. 当前实际问题已收口到 `services/sim-trading/Dockerfile` 单文件，根因方向聚焦于 Docker locale / apt 构建阶段。
3. 鉴于此前曾出现越界修改痕迹，本轮先补齐正式执行批次冻结，再交由对应服务 Agent 在合规白名单内实施。

### 2. 本轮执行口径

1. 执行批次：**补充批次 A1**
2. 执行 Agent：**模拟交易**
3. 保护级别：**P1**
4. 业务白名单：`services/sim-trading/Dockerfile`
5. 目标收口：仅修复 Docker locale / apt 构建问题，并完成本地 `docker build` 最小自校验。
6. 本批次不包含 `docker-compose.dev.yml`、任一 `.env.example`、远端 Mini 部署、Secret 注入或其他服务改动。

### 3. 本轮继续禁止

1. 不得修改 `docker-compose.dev.yml`。
2. 不得修改 `services/sim-trading/.env.example`。
3. 不得修改 `services/sim-trading/requirements.txt`、`src/**`、`tests/**`、`configs/**` 或该服务内其他非白名单文件。
4. 不得修改 `services/dashboard/**` 或任何其他服务目录。
5. 不得把 locale / apt 问题扩展解释为 compose、环境模板或远端 Mini 运维问题。
6. 若执行中需要第 2 个业务文件，当前批次立即失效，必须回交补充预审。

### 4. 本批次验收标准

1. `services/sim-trading/Dockerfile` 单文件热修完成。
2. 本地 `docker build` 可完成最小构建自校验，构建问题收口于 locale / apt。
3. 无白名单外业务文件写入。
4. 终审前不得宣称 Mini 部署闭环或 `TASK-0017` 整体闭环。

---

## 十、预审结论

1. **`TASK-0017` 正式成立。**
2. **F Docker 化与 Mini 部署必须作为独立部署任务推进，不得与 `TASK-0011` legacy 清退混并。**
3. **在文件级白名单与 Mini 运维授权补齐前，本任务暂不进入代码 Token 或远端执行。**
4. **2026-04-06 已补充冻结 A1 单文件 P1 执行批次；当前仅建议为模拟交易 Agent 签发 `services/sim-trading/Dockerfile` 的单文件 Token。**

---

## 十一、补充批次 A3 — amd64 locale 修复与 platform 指定（2026-04-07）

### 1. 补充背景

1. 补充批次 A1 已完成 Dockerfile locale / apt 构建热修，但执行后发现容器内 CTP C++ 库在 amd64 环境下仍触发 `locale::facet::_S_create_c_locale name not valid` 并 abort。
2. 根因定位：`python:3.11-slim` 镜像中不存在 `C.UTF-8` locale；该 locale 需要额外安装 locales 包；glibc 内置的 `C` locale 在任何系统均可用，无需额外包。
3. 补充批次 A2 扩展白名单已将 `docker-compose.dev.yml`（`platform: linux/amd64`）纳入，但该项尚未独立执行提交；本 A3 批次将两个精确修复收口到同一执行批次，统一签发、统一提交、独立回滚。

### 2. 本批次变更目标

| 序号 | 文件路径 | 变更内容 | 保护级别 |
|------|---------|---------|---------|
| 1 | `services/sim-trading/Dockerfile` | 将 `ENV LANG=C.UTF-8` 改为 `ENV LANG=C`；将 `ENV LC_ALL=C.UTF-8` 改为 `ENV LC_ALL=C` | P1 |
| 2 | `docker-compose.dev.yml` | 仅在 sim-trading 服务段内新增 `platform: linux/amd64` 一行（若 A2 扩展已执行则确认已含，若否则此次补入） | P0 |

### 3. 变更理由

1. **`services/sim-trading/Dockerfile`（P1）**：`C.UTF-8` 在 `python:3.11-slim`（Debian bookworm-slim）中不存在；CTP C++ 共享库在 amd64 容器内加载时尝试设置该 locale 导致 abort。`LANG=C` / `LC_ALL=C` 是 glibc 内置 locale，无需任何额外包，且满足 CTP 库的最低 locale 要求。
2. **`docker-compose.dev.yml`（P0）**：M 芯片 Mac 默认拉 arm64 镜像，openctp-ctp 目前仅提供 amd64 轮子。不加 `platform: linux/amd64` 时构建失败或运行时 segment fault。该字段为部署级热修，不引入新服务逻辑或 Secret。

### 4. 执行约束

1. 两个文件须独立提交，独立回滚：P1（Dockerfile）与 P0（docker-compose.dev.yml）不得合并为同一 git commit。
2. 执行 Agent：
   - `services/sim-trading/Dockerfile`（P1）：模拟交易 Agent（须持有有效 P1 Token）。
   - `docker-compose.dev.yml`（P0）：Jay.S 指定角色（须持有有效 P0 Token）；已由 TASK-0017 A2 扩展签发的 P0 Token 如仍有效可复用，否则须重新签发。
3. 执行完毕后须通过本地 `docker build --platform linux/amd64` 最小构建自校验，容器启动后 `/health` 端点正常响应，方可宣告本批次通过。
4. 本批次与 `docker-compose.dev.yml` 的任何其他内容改动均无关；仅限 `platform: linux/amd64` 一行（sim-trading 服务段），不得改动其他服务或字段。
5. 若执行中发现需要第 3 个业务文件，本批次立即失效并回交补充预审。

### 5. 预审结论

1. **预审通过。**
2. 本批次白名单：`services/sim-trading/Dockerfile`（P1）、`docker-compose.dev.yml`（P0）。
3. Token 状态：**pending_token** — `services/sim-trading/Dockerfile` 须由 Jay.S / Atlas 为模拟交易 Agent 签发 P1 Token；`docker-compose.dev.yml` 须单独签发 P0 Token（可复用 A2 扩展已签发的 P0 Token，如仍有效）。
4. 执行前置：本 A3 批次相对 A1/A2 无强制顺序依赖，可与 A2 剩余 Token 签发并行推进；但 P0 与 P1 须分别签发、独立提交。
5. 签名：项目架构师，2026-04-07。