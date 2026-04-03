# TASK-0003 预审 Review

## Review 信息

- 任务 ID：TASK-0003
- 审核角色：项目架构师
- 审核阶段：建档 + 阶段一草稿自校验完成
- 审核时间：2026-04-03
- 审核结论：通过（建档合规；四份草稿已完成并通过自校验；P0 正式写入仍待 Token；Q1～Q5 待 Jay.S 确认后方可开始批次 A）

## 核验内容

### 边界核验

- 回测服务旧口径（离线研究）已明确修正为"在线 TqSdk 路径"，README 将随批次 A Token 一并修正。✅
- 项目架构师仅负责阶段一契约草稿与派发，不进入 `services/backtest/` 代码写入。✅
- 回测 Agent 负责阶段二全部 Python 后端与部署文件，分批次派发。✅
- `docker-compose.dev.yml` 与 `services/backtest/.env.example` 均为 P0 保护文件，需单独走 P0 Token，不随批次 C 代码并入。✅
- 本轮建档与草稿区写入未触及任何 P0/P1 保护目录。✅

### 文件白名单核验

- `docs/tasks/TASK-0003-*.md`：P-LOG 区，项目架构师可写。✅
- `docs/reviews/TASK-0003-review.md`：P-LOG 区，项目架构师可写。✅
- `docs/locks/TASK-0003-lock.md`：P-LOG 区，项目架构师可写。✅
- `docs/rollback/TASK-0003-rollback.md`：P-LOG 区，项目架构师可写。✅
- `docs/handoffs/TASK-0003-*.md`：P-LOG 区，项目架构师可写。✅
- `shared/contracts/drafts/backtest/`：草稿区，当前批次可写，无需 Token。✅
- `shared/contracts/backtest/`：P0 区，当前不写入，待 Token。⏳
- `services/backtest/src/`：P1 区，待批次分批 Token，回测 Agent 执行。⏳
- `docker-compose.dev.yml`：P0 区，批次 C 前单独 Token。⏳
- `services/backtest/.env.example`：P0 区，Q2 确认后单独 Token。⏳

### 阶段一草稿自校验结论

- `backtest_job.md`：字段覆盖 TqBacktest 必要配置；已排除 TqSdk 内部实现字段、策略层参数、真实账户字段。✅
- `backtest_result.md`：字段仅保留外部可见结果指标与文件路径；不含 TqSdk 内部状态与归档实现字段。✅
- `performance_metrics.md`：字段与 legacy `PerformanceMetrics` 模型一一对应；已排除进阶分析字段（walk-forward、overfitting）；风险利率为计算配置项，不作为结果字段。✅
- `api.md`：7 个最小 MVP 端点（health + 任务 CRUD + 结果查询 + 指标 + 权益曲线）；已排除参数扫描、walk-forward、批量管理、WebSocket、管理员接口。✅
- 四份草稿均未引入 legacy 业务逻辑，未绑定 TqSdk 内部实现细节。✅

### 强制约束核验

- TqSdk 在线回测路径已在 TASK-0003 任务文件中明确列为强制约束。✅
- 批次拆分满足"单批次最多 5 文件"治理规则（批次 A：5，批次 B：5，批次 C：5 + 需单独 Token 的 2 个 P0 受保护文件）。✅
- 各批次对应独立提交，支持独立回滚。✅

### 风险矩阵

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| 回测 Agent 复用 legacy 本地数据路径 | P0 | 强制约束已明确，草稿区不含 legacy 逻辑，代码审查时检查 |
| Q1-Q5 未确认就开始批次 A 写入 | P1 | 批次 A P1 Token 签发前，项目架构师提醒 Jay.S 确认 Q1 |
| `docker-compose.dev.yml` 被顺带修改 | P0 | 锁记录与 Token 分离申请已明确 |
| V0 看板目录名空格导致部署路径错误 | P2 | Q3 确认后统一改名，在批次 C 前执行 |
| TqAuth 凭证明文写入代码 | P0 | 凭证必须只来自环境变量，代码审查时检查 |

## P0 Token 申请清单（阶段一）

- `shared/contracts/backtest/backtest_job.md`
- `shared/contracts/backtest/backtest_result.md`
- `shared/contracts/backtest/performance_metrics.md`
- `shared/contracts/backtest/api.md`

## 下一步

1. Jay.S 签发 P0 Token → 项目架构师执行阶段一正式迁移与终审锁回。
2. Jay.S 确认 Q1（至少）→ 项目架构师申请批次 A P1 Token，回测 Agent 开始批次 A。
3. 批次 A 终审通过 → 申请批次 B P1 Token。
4. 批次 B 终审通过，Jay.S 确认 Q2 → 申请批次 C 相关 P0/P1 Token。
