# TASK-0005 Review

## Review 信息

- 任务 ID：TASK-0005
- 审核角色：项目架构师
- 审核阶段：backtest 容器命名预审
- 审核时间：2026-04-04
- 审核结论：通过（范围冻结为 `services/backtest/` 单服务；当前最小业务白名单仅 `services/backtest/docker-compose.yml`；本轮仅允许修改 Docker Compose 中的容器命名字段；命名冻结为 `JBT-BACKTEST-8103` / `JBT-BACKTEST-3001`；运行态 `botquant-backtest-api:8004` 仅作执行侧例外，不进入仓内白名单；当前可进入 Jay.S 单文件 P1 Token 即时确认准备态）

---

## 一、任务边界核验

1. 任务目标明确：统一 backtest 容器命名规范为 `JBT-BACKTEST-端口` 全大写格式。
2. 任务目录明确：仅限 `services/backtest/`。
3. 本轮唯一允许修改的业务文件为 `services/backtest/docker-compose.yml`。
4. 本轮明确禁止扩展到：
   - `docker-compose.dev.yml`
   - `services/backtest/Dockerfile`
   - `services/backtest/backtest_web/**`
   - `services/backtest/.env.example`
   - `services/backtest/src/**`
   - `services/backtest/tests/**`
   - `shared/contracts/**`
   - `services/*` 其他目录
5. 本轮不做前端页面改动，不做 contracts 改动，不做跨服务实现，不做根级 compose 调整。

## 二、只读技术结论

1. `services/backtest/docker-compose.yml` 当前存在两个容器定义：`backtest-api` 与 `backtest-dashboard`。✅
2. 当前 `container_name` 分别为 `backtest-api` 与 `backtest-dashboard`，尚未进入 JBT 全大写命名规范。✅
3. 当前端口映射已经固定为 `8103` 与 `3001`，足以直接支撑命名冻结为按端口命名。✅
4. 当前 `image`、`environment`、`depends_on`、`healthcheck`、`volumes`、`networks` 字段并非本轮阻塞项，不需要纳入变更目标。✅
5. 当前运行态临时 API 容器 `botquant-backtest-api:8004` 可作为执行态例外处理，但不构成仓内业务文件白名单的一部分。✅

## 三、白名单冻结

### 建议签发的 P1 业务文件白名单

1. `services/backtest/docker-compose.yml`

### 当前不建议纳入的文件

1. `docker-compose.dev.yml`
2. `services/backtest/Dockerfile`
3. `services/backtest/backtest_web/**`
4. `services/backtest/.env.example`
5. `services/backtest/src/**`
6. `services/backtest/tests/**`
7. `shared/contracts/**`

### 不扩白名单的判断依据

1. 当前目标仅为容器命名统一，单文件即可完成。
2. 命名冻结不依赖镜像、端口、页面、环境变量或服务代码修改。
3. 运行态 `8004` 容器例外若需处理，应在运行环境完成，而不是通过扩仓内白名单实现。

## 四、命名规范冻结

1. API 容器：`JBT-BACKTEST-8103`
2. Dashboard 容器：`JBT-BACKTEST-3001`
3. 当前运行中的临时 API 容器 `botquant-backtest-api:8004` 可例外更名为 `JBT-BACKTEST-8004`。
4. 上述 `8004` 例外仅属于运行态口径，不进入仓内业务白名单，不构成额外文件授权。

## 五、执行 Agent 建议

- **合规默认建议：回测 Agent。**

理由：

1. 唯一白名单文件仍位于 `services/backtest/` 目录内。
2. 本轮是 backtest 服务自身 compose 命名调整，不应由项目架构师代写。
3. 若需要执行运行态 `8004` 容器更名，也应由回测 Agent 结合同一服务上下文处理。

## 六、风险与缓解

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| 顺手修改 `image`、`ports`、`environment`、`depends_on` 等非命名字段 | P1 | Token 严格限制为单文件，并在 review 中冻结“只改容器命名字段” |
| 把根级 `docker-compose.dev.yml` 一并纳入 | P0 | 预审明确排除根级 compose；若必须调整，必须另开补充预审 |
| 以处理 `8004` 运行态容器为由扩白名单到脚本或 Dockerfile | P1 | 明确 `8004` 仅为执行态例外，不进入仓内业务白名单 |
| 将命名统一任务顺手扩展到前端页面文件或其他服务 | P1 | 预审已冻结“仅 `services/backtest/docker-compose.yml` 单文件”，超范围即中止 |

## 七、预审结论

1. **TASK-0005 预审通过。**
2. **本轮可进入 Jay.S 单文件 P1 Token 即时确认准备态。**
3. **建议签发单 Agent、单任务、单文件的 P1 Token。**
4. **当前公共状态应补充为“TASK-0005 backtest 容器命名统一已预审，待 Jay.S 对 `services/backtest/docker-compose.yml` 作本轮即时执行确认”。**
