# TASK-0017 Lock 记录

## Lock 信息

- 任务 ID：TASK-0017
- 阶段：sim-trading Docker 化与 Mini 部署预审
- 当前任务是否仍处于“预审未执行”状态：整体是；补充批次 A1 已冻结待签发
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - 对应服务 Agent（后续仓内 Docker 文件实现）
  - Atlas（后续远端 Mini 运维执行，但需 Jay.S 明确授权）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `services/sim-trading/**` / `services/dashboard/**` 中 Docker 相关文件：后续 P1 Token
  - `docker-compose.dev.yml`：后续 P0 Token
  - 各服务 `.env.example`：后续 P0 Token
  - 远端 Mini 运维动作：不适用 Git Token，但必须有 Jay.S 明确运维授权

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0017-sim-trading-Docker化与Mini部署预审.md`
2. `docs/reviews/TASK-0017-review.md`
3. `docs/locks/TASK-0017-lock.md`
4. `docs/rollback/TASK-0017-rollback.md`
5. `docs/handoffs/TASK-0017-Docker与Mini部署预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `services/sim-trading/**`（除补充批次 A1 待签发的 `services/sim-trading/Dockerfile` 外，其余全部继续锁定）
2. `services/dashboard/**`
3. `docker-compose.dev.yml`
4. `services/sim-trading/.env.example`
5. `services/dashboard/.env.example`
6. 远端 Mini 的容器启停、镜像切换、Secret 注入与回滚验证动作
7. 其他全部非白名单文件

## 补充批次 A1 冻结信息（2026-04-06）

1. 批次名称：补充批次 A1
2. 执行 Agent：模拟交易
3. 保护级别：P1
4. 唯一业务白名单：`services/sim-trading/Dockerfile`
5. 批次目标：仅修复 Docker locale / apt 构建问题，并完成本地 `docker build` 最小自校验。
6. 当前 Token 状态：未签发；进入执行前须由 Jay.S / Atlas 按单文件范围 issue。

---

## 补充批次 A2 冻结信息（2026-04-06）

1. 批次名称：补充批次 A2 — 启动自动连接（startup auto-connect）
2. 执行 Agent：模拟交易
3. 保护级别：P1
4. 业务白名单：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/src/main.py`
5. 批次目标：
   - `router.py`：初始化 `_system_state` 时从 `os.getenv("SIMNOW_USER_ID","")` / `os.getenv("SIMNOW_PASSWORD","")` / `os.getenv("SIMNOW_BROKER_ID","9999")` 读取值，替换空字符串硬编码。
   - `main.py`：新增 `@app.on_event("startup")` async 函数，`SIMNOW_USER_ID` 非空时自动触发 CTP 连接，宽捕获所有异常静默失败。
6. 签名：项目架构师
7. 建档时间：2026-04-06
8. 当前 Token 状态：pending_token；进入执行前须由 Jay.S / Atlas 按双文件范围 issue；A1 Token 签发与自校验须先于 A2 完成。

---

## 补充批次 A2 白名单扩展冻结（2026-04-06）

1. **扩展时间**：2026-04-06
2. **签名**：项目架构师
3. **扩展后 A2 完整业务白名单**：
   - `services/sim-trading/src/api/router.py`（P1，原有）
   - `services/sim-trading/src/main.py`（P1，原有）
   - `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`（P1，本次新增）
   - `docker-compose.dev.yml`（P0，本次新增）
4. **新增文件变更目标**：
   - `intelligence/page.tsx`：删除"2/5"连续亏损计数与"60%"保证金水位两处硬编码 mock 数据，改为动态 state；API 未接入时显示「--」，不得显示任何 mock 数值。
   - `docker-compose.dev.yml`：仅在 sim-trading 服务段添加 `platform: linux/amd64` 一行，不修改其他服务或任何其他字段。
5. **保护级别**：P1（前三文件）；P0（`docker-compose.dev.yml`，须单独签发 Token，独立提交独立回滚）
6. **执行 Agent**：模拟交易（P1 三文件）；Jay.S 指定角色（P0 文件）
7. **当前 Token 状态**：pending_token；P1 三文件须按扩展后范围由 Jay.S 重新签发 P1 Token；`docker-compose.dev.yml` 须单独签发 P0 Token；A1 Token 签发与自校验须先于 A2 执行。

## 当前继续禁止修改的路径说明

1. 禁止把本任务与 `TASK-0011` legacy 清退混并。
2. 禁止在没有文件级白名单的情况下修改任何服务 Docker 文件或根级 compose。
3. 禁止把真实 Secret 烘焙进镜像、compose、`.env.example` 或治理账本。
4. 禁止在未获 Jay.S 明确授权前执行任何远端 Mini 运维动作。

## 进入执行前需要的 Token / 授权

1. 补充批次 A1 需先由 Jay.S / Atlas 为模拟交易 Agent 签发单文件 P1 Token，文件仅限 `services/sim-trading/Dockerfile`。
2. `TASK-0009`、`TASK-0013`、`TASK-0010`、`TASK-0014`、`TASK-0015`、`TASK-0016` 的部署主线前置条件仍需另外满足。
3. 若后续要扩大到其他服务 Docker 文件、`docker-compose.dev.yml` 或 `.env.example`，必须重新冻结分批文件级白名单，再由 Jay.S 签发对应 P1 / P0 Token。
4. Jay.S 还需确认 Mini 部署窗口、远端 Secret 注入方案与是否同时包含 `services/dashboard/**` 部署。
5. Atlas 在执行远端步骤前，必须先获得逐条运维授权。

## 当前状态

- 预审状态：已通过
- Token 状态：主任务未申请代码 Token；补充批次 A1 待签发单文件 P1 Token；补充批次 A2 扩展后白名单四文件 — P1 三文件（`router.py` + `main.py` + `intelligence/page.tsx`）待签发 P1 Token，`docker-compose.dev.yml` 待单独签发 P0 Token（pending_token）；补充批次 A3 (`Dockerfile` P1 + `docker-compose.dev.yml` P0) 已预审通过，pending_token
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行或远端运维阶段

## 补充批次 A3 冻结信息（2026-04-07）

1. 批次名称：补充批次 A3 — amd64 locale 修复与 platform 指定
2. 执行 Agent：模拟交易（P1 文件）；Jay.S 指定角色（P0 文件）
3. 保护级别：P1（`services/sim-trading/Dockerfile`）；P0（`docker-compose.dev.yml`）
4. 业务白名单：
   - `services/sim-trading/Dockerfile`（P1）
   - `docker-compose.dev.yml`（P0）
5. 批次目标：
   - `Dockerfile`：将 `ENV LANG=C.UTF-8` 改为 `ENV LANG=C`；将 `ENV LC_ALL=C.UTF-8` 改为 `ENV LC_ALL=C`。原因：`C.UTF-8` 在 `python:3.11-slim` 中不存在，导致 CTP C++ 库在 amd64 容器内 abort；`LANG=C` 为 glibc 内置，无需额外 package。
   - `docker-compose.dev.yml`：仅在 sim-trading 服务段添加 `platform: linux/amd64` 一行，使 M 芯片 Mac 通过 Rosetta 2 运行 x86_64 容器，openctp-ctp 才能正确安装并运行。
6. 签名：项目架构师
7. 建档时间：2026-04-07
8. 当前 Token 状态：pending_token；`Dockerfile`（P1）须由 Jay.S / Atlas 为模拟交易 Agent 签发 P1 Token；`docker-compose.dev.yml`（P0）须单独签发 P0 Token（可复用 A2 扩展已签发 P0 Token，如仍有效）；两文件可并行签发但须独立提交、独立回滚，不得合并 commit。

## 结论

**TASK-0017 整体仍处于"预审未执行"状态；补充批次 A1（`services/sim-trading/Dockerfile`，单文件 P1）与补充批次 A2（扩展后四文件：`router.py`、`main.py`、`intelligence/page.tsx` 三文件 P1 + `docker-compose.dev.yml` 单文件 P0）均已冻结且 A2 已完成扩展预审，全部待签发；补充批次 A3（`Dockerfile` P1 + `docker-compose.dev.yml` P0，amd64 locale 修复与 platform 指定）已于 2026-04-07 完成预审，pending_token；A3 可与 A2 剩余 Token 签发并行推进，但 P0 与 P1 须分别签发、独立提交、独立回滚；其余仓内 Docker 路径、服务环境模板与远端 Mini 运维动作继续锁定。**