# TASK-0006 Review

## Review 信息

- 任务 ID：TASK-0006
- review-id：REVIEW-TASK-0006（预审阶段）
- 审核角色：项目架构师
- 审核阶段：预审（建档与白名单冻结）
- 审核时间：2026-04-04
- 审核结论：**预审通过**，白名单 4 文件已冻结，待 Jay.S 签发 Token 后方可执行

---

## 一、任务边界核验

1. 任务归属明确：Docker 配置文件归属 `services/backtest/`，契约修改归属 `shared/contracts/backtest/`，均有明确服务边界。
2. 本轮目标范围明确：
   - 新建 3 个 Docker 相关文件（`Dockerfile` × 2，`docker-compose.yml` × 1）
   - 修改 1 个已有契约文件（`shared/contracts/backtest/api.md`，仅"当前任务输入口径"节）
3. 本轮明确不纳入：
   - `docker-compose.dev.yml`（根目录 P0，继续冻结）
   - `services/backtest/.env.example`（P0，继续冻结）
   - `services/backtest/src/backtest/**` 已锁回的业务文件
   - 其他 `shared/contracts/**` 文件（仅允许改 `api.md`）
   - 其他服务目录

## 二、技术边界核验

1. backtest Dockerfile 将从 `.env.example` 标注的环境变量读取配置，不硬编码任何凭证。✅（承诺约束）
2. 看板 Dockerfile 不引入 TqSdk 凭证，仅执行前端静态构建 + `next start`。✅（安全边界清晰）
3. `api.md` 修改范围明确限定在"当前任务输入口径"节，追加通用模板支持说明，不改动其他已冻结字段。✅
4. `docker-compose.yml` 包含两个服务（backtest-api 8103、backtest-dashboard 3001），均设置 `restart: always`，符合 D-BT-05 同机同 compose 原则。✅

## 三、保护区合规性核验

1. `shared/contracts/**` 属于 P0 保护区，修改 `api.md` 需单独 P0 Token。
2. Jay.S 已明确要求完成此工作，视为已授权，但仍须走正式 Token 签发流程。
3. 建议签发方式：P1 Token（3 个新建文件）+ P0 Token（api.md），或合并为一枚同范围 Token（由 Jay.S 确认）。

## 四、白名单冻结结论

| # | 文件 | 操作 | 保护级别 | 结论 |
|---|---|---|---|---|
| 1 | `services/backtest/Dockerfile` | 新建 | P1 | 通过 |
| 2 | `services/backtest/V0-backtext 看板/Dockerfile` | 新建 | P1 | 通过 |
| 3 | `services/backtest/docker-compose.yml` | 新建 | P1 | 通过 |
| 4 | `shared/contracts/backtest/api.md` | 修改（限定节） | P0 | 通过，需 P0 Token |

共 4 文件，在 WORKFLOW 5 文件上限内。

## 五、风险与注意事项

1. **凭证安全**：backtest Dockerfile 必须通过 `ENV` 或 `docker-compose.yml` 的 `env_file` 引用环境变量，严禁 `COPY .env` 或任何形式的凭证硬编码；终审时需逐行核查。
2. **契约一致性**：`api.md` 追加通用模板说明后，需确认与 `backtest_job.md` 中 `strategy_template_id` 字段描述保持一致，不引入歧义。
3. **远端部署**：Docker 推送与 `docker-compose up -d` 属于远端执行，不属于文件写操作，不需要额外 Token，但需确认远端环境已安装 Docker + Docker Compose。

## 六、预审结论

- **结论**：预审通过
- **白名单**：已冻结 4 文件（见第四节）
- **下一步**：Jay.S 签发 Token（P1 × 3 文件 + P0 × 1 文件，可合并签发）→ 回测 Agent 执行 → 终审 → lockback
