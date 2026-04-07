# TASK-0017 Review

## Review 信息

- 任务 ID：TASK-0017
- 审核角色：项目架构师
- 审核阶段：sim-trading Docker 化与 Mini 部署预审
- 审核时间：2026-04-06
- 审核结论：通过（主任务部署治理冻结保持有效；2026-04-06 已补充冻结 A1 单文件 P1 执行批次，待 Jay.S / Atlas 为模拟交易 Agent 签发 Token）

---

## 一、任务目标

1. 冻结 Docker 化、Mini 部署与切换前验证的正式边界。
2. 冻结 `TASK-0017` 与 `TASK-0011` legacy 清退的任务分界。
3. 冻结未来服务文件、`docker-compose.dev.yml`、`.env.example` 与远端运维动作的保护级别划分。

## 二、当前轮次白名单

1. `docs/tasks/TASK-0017-sim-trading-Docker化与Mini部署预审.md`
2. `docs/reviews/TASK-0017-review.md`
3. `docs/locks/TASK-0017-lock.md`
4. `docs/rollback/TASK-0017-rollback.md`
5. `docs/handoffs/TASK-0017-Docker与Mini部署预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 三、当前轮次代码 Token 策略

1. 当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。
2. 后续若修改 `services/sim-trading/**` 或 `services/dashboard/**` 中的 Docker 相关服务文件，需要 P1 Token。
3. 后续若修改 `docker-compose.dev.yml`，需要 P0 Token。
4. 后续若修改各服务 `.env.example`，需要 P0 Token。
5. 远端 Mini 的容器启停、Secret 注入、镜像切换与回滚验证不适用 Git Token，但必须有 Jay.S 明确运维授权。

## 四、当前轮次通过标准

1. 已冻结 `TASK-0017` 与 `TASK-0011` 的边界，明确部署完成不等于允许清退 legacy。
2. 已冻结未来 Docker / compose / `.env.example` / 远端运维的拆批与保护级别口径。
3. 已冻结 Mini 部署前必须验证的健康检查、只减仓、通知、上游接入和回滚路径。
4. 已明确所有 Secret 只能运行时注入，不得入 Git、镜像、compose 或治理账本。

## 五、当前轮次未进入代码执行的原因

1. 本任务当前轮次只做部署治理冻结，不做仓内 Docker 实现或远端部署。
2. `TASK-0009`、`TASK-0013`、`TASK-0010`、`TASK-0014`、`TASK-0015`、`TASK-0016` 都是进入部署前置条件。
3. 当前尚未冻结 `services/sim-trading/**`、`services/dashboard/**`、`docker-compose.dev.yml` 与各服务 `.env.example` 的文件级白名单。
4. 当前没有任何针对仓内保护路径的 P0 / P1 Token，也没有 Jay.S 明确批准的 Mini 运维执行窗口。

## 六、补充批次 A1 执行批次冻结（2026-04-06）

1. 现已把 `services/sim-trading/Dockerfile` 追加冻结为 `TASK-0017` 的**补充批次 A1**。
2. 执行 Agent 固定为**模拟交易**，保护级别固定为**P1**。
3. 本批次唯一业务白名单为 `services/sim-trading/Dockerfile`。
4. 变更目标仅限修复 Docker locale / apt 构建问题，并完成本地 `docker build` 最小自校验。
5. `docker-compose.dev.yml`、`services/sim-trading/.env.example`、`services/sim-trading/requirements.txt`、其他 `services/**` 文件、远端 Mini 运维动作均不在本批次范围内。
6. 若执行中需要第 2 个业务文件，或需要扩展到 compose / `.env.example` / 远端部署，本批次立即失效并回交补充预审。

## 七、预审结论

1. **TASK-0017 预审通过。**
2. **当前轮次只完成 Docker 与 Mini 部署治理冻结，不进入代码执行或远端运维执行。**
3. **后续进入实施前，必须先补齐白名单、P0 / P1 Token 与 Mini 运维授权。**
4. **补充批次 A1 已冻结待签发；当前唯一建议进入执行的业务文件为 `services/sim-trading/Dockerfile`。**
5. **补充批次 A2 已于 2026-04-06 完成预审，待 Jay.S / Atlas 为模拟交易 Agent 签发双文件 P1 Token。**

---

## 八、补充批次 A2 预审通过记录（2026-04-06）

1. **批次名称**：补充批次 A2 — 启动自动连接（startup auto-connect）
2. **审核时间**：2026-04-06
3. **签名**：项目架构师
4. **审核结论**：通过
5. **审核要点**：
   a. `router.py` 初始化 `_system_state` 时改读 `os.getenv` 为纯环境变量注入，不写入任何真实凭证，符合敏感信息治理口径。
   b. `main.py` `startup` 函数使用宽捕获 `except Exception` 静默失败，确保 CTP 连接异常不会 crash 服务，符合启动安全要求。
   c. A2 变更范围已固定为两个文件；若执行中出现第 3 个业务文件，批次立即失效并回交补充预审。
   d. 上述修改均属纯配置化改造与启动自动化，不属于风控逻辑变更，不触发额外 P0 审核。
6. **唯一业务白名单**：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/src/main.py`
7. **保护级别**：P1
8. **执行 Agent**：模拟交易
9. **当前 Token 状态**：pending_token，进入执行前须由 Jay.S / Atlas 按双文件范围 issue。

---

## 九、补充批次 A2 白名单扩展预审通过记录（2026-04-06）

1. **扩展时间**：2026-04-06
2. **签名**：项目架构师
3. **扩展结论**：预审通过
4. **扩展要点**：
   a. `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`：消除两处硬编码 mock 数据（连续亏损计数 `2/5`、保证金水位 `60%`）改为动态 state；未接入时显示「--」。属于前端数据可信度修复，不涉及风控逻辑，保护级别 P1。
   b. `docker-compose.dev.yml`：为 sim-trading 服务块添加 `platform: linux/amd64`，解决 M 芯片 Mac 上 openctp-ctp amd64-only 轮子无法在 arm64 容器内运行的问题。属于部署级热修，不引入新服务逻辑或 Secret，保护级别 P0。
   c. `docker-compose.dev.yml` 属根级 compose，依本任务"五-2"原则本应单独 P0 批次，本次纳入 A2 扩展，但须与 P1 Token 分别签发，P0 文件独立提交独立回滚。
   d. 扩展范围已固定为四个文件；若执行中出现第 5 个业务文件，A2 扩展批次立即失效并回交补充预审。
5. **扩展后 A2 完整业务白名单**：
   - `services/sim-trading/src/api/router.py`（P1，原有）
   - `services/sim-trading/src/main.py`（P1，原有）
   - `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`（P1，本次新增）
   - `docker-compose.dev.yml`（P0，本次新增，须单独 P0 Token）
6. **Token 状态**：pending_token；P1 三文件须按扩展后范围由 Jay.S 重新签发 P1 Token；`docker-compose.dev.yml` 须单独签发 P0 Token；A1 Token 签发与自校验须先于 A2 执行。

---

## 十、补充批次 A3 预审通过记录（2026-04-07）

1. **批次名称**：补充批次 A3 — amd64 locale 修复与 platform 指定
2. **审核时间**：2026-04-07
3. **签名**：项目架构师
4. **审核结论**：通过
5. **审核要点**：
   a. `services/sim-trading/Dockerfile`：将 `ENV LANG=C.UTF-8` / `ENV LC_ALL=C.UTF-8` 改为 `ENV LANG=C` / `ENV LC_ALL=C`。`python:3.11-slim` 镜像不含 `C.UTF-8` locale，CTP C++ 库在 amd64 容器加载时触发 `locale::facet::_S_create_c_locale name not valid` abort；`LANG=C` 为 glibc 内置，无需额外 package，满足 CTP 库最低 locale 要求。符合最小改动原则，不触发额外 P0 审核。
   b. `docker-compose.dev.yml`：仅为 sim-trading 服务段新增 `platform: linux/amd64`，使 M 芯片 Mac 通过 Rosetta 2 运行 x86_64 容器。该字段为部署级热修，不引入新服务逻辑或 Secret，不改动其余服务段或任何其他字段。
   c. 两文件须独立提交、独立回滚：P1（Dockerfile）与 P0（docker-compose.dev.yml）不得合并 commit。
   d. A3 变更范围已固定为两个文件；若执行中出现第 3 个业务文件，批次立即失效并回交补充预审。
6. **本批次业务白名单**：
   - `services/sim-trading/Dockerfile`（P1）
   - `docker-compose.dev.yml`（P0）
7. **执行 Agent**：
   - `services/sim-trading/Dockerfile`（P1）：模拟交易
   - `docker-compose.dev.yml`（P0）：Jay.S 指定角色（可复用 A2 扩展已签发 P0 Token，如仍有效）
8. **当前 Token 状态**：pending_token；`Dockerfile` 须签发 P1 Token；`docker-compose.dev.yml` 须签发 P0 Token（或确认 A2 扩展 P0 Token 仍有效）；两者可并行签发，但须分别独立提交。