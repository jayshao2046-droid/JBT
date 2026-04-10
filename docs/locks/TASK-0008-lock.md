# TASK-0008 Lock 记录

## Lock 信息

- 任务 ID：TASK-0008
- 阶段：✅ A~D 四批全部实施完成并锁回 [2026-04-10 收口]
- 执行口径：
  - Atlas：本轮当前会话直修 / 主导实现
  - 项目架构师：预审、边界冻结、公共状态同步与后续终审留痕
  - 回测 Agent：补写私有 prompt、handoff 与服务侧实施记录
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - 批次 A `shared/contracts/backtest/api.md`：✅ locked (tok-6739689c)
  - 批次 B 5 文件正式引擎核心：✅ locked (tok-7bb948e5)
  - 批次 C 5 文件正式结果 / API / 报告导出并回：✅ locked (tok-33baea65)
  - 批次 D 4 文件前端导出链路：✅ locked (tok-5ec15b54)

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0008-backtest-泛化正式引擎与正式报告导出预审.md`
2. `docs/reviews/TASK-0008-review.md`
3. `docs/locks/TASK-0008-lock.md`
4. `docs/handoffs/TASK-0008-泛化正式引擎预审交接单.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

说明：

1. 上述 6 个文件均属于 P-LOG 协同账本区，不使用文件级 Token。
2. 本轮未扩写 `docs/rollback/**`。
3. 本轮不伪造任何 `token_id`；当前只记录“待 Jay.S 按批次签发 Token”的治理状态。

## 批次 A 业务文件白名单（待 P0 Token）

1. `shared/contracts/backtest/api.md`

## 批次 B 业务文件白名单（待 P1 Token）

1. `services/backtest/src/backtest/strategy_base.py`
2. `services/backtest/src/backtest/factor_registry.py`
3. `services/backtest/src/backtest/generic_strategy.py`
4. `services/backtest/src/backtest/runner.py`
5. `services/backtest/tests/test_generic_strategy_pipeline.py`

## 批次 C 业务文件白名单（待 P1 Token）

1. `services/backtest/src/backtest/result_builder.py`
2. `services/backtest/src/api/routes/backtest.py`
3. `services/backtest/src/api/routes/strategy.py`
4. `services/backtest/src/api/routes/support.py`
5. `services/backtest/tests/test_formal_report_api.py`

## 批次 D 业务文件白名单（待 P1 Token）

1. `services/backtest/backtest_web/src/utils/api.ts`
2. `services/backtest/backtest_web/app/agent-network/page.tsx`
3. `services/backtest/backtest_web/app/operations/page.tsx`
4. `services/backtest/backtest_web/src/utils/reportExport.ts`

## 当前继续锁定的重点文件

1. TASK-0004 当前全部既有业务白名单文件
2. TASK-0007 当前全部既有业务白名单文件
3. `shared/contracts/backtest/backtest_job.md`
4. `shared/contracts/backtest/backtest_result.md`
5. `shared/contracts/backtest/performance_metrics.md`
6. `services/backtest/src/backtest/fc_224_strategy.py`
7. `docker-compose.dev.yml`
8. `services/backtest/Dockerfile`
9. `services/backtest/src/api/app.py`
10. 其他全部非白名单文件

## 锁控说明

1. TASK-0004 / TASK-0007 的白名单与 Token 不覆盖 TASK-0008；本事项必须独立签发、独立实施、独立 lockback。
2. 批次 A 属于 P0，必须先于批次 B / C / D 执行；不得跳过顺序。
3. 批次 B 白名单严格冻结为 5 文件；若执行中需要 `fc_224_strategy.py`、额外表达式引擎文件或任何第 6 个业务文件，当前 Token 立即失效，必须回交补充预审。
4. 批次 C 只允许处理正式结果、正式报告导出与 API 并回；若执行中需新增 contract 字段或第 6 个业务文件，也必须补充预审。
5. 批次 D 当前冻结 4 文件；若执行中新增任一白名单外前端 helper / 模板 / 文档文件，也必须补充预审，不得以“未达到 6 文件上限”为由跳过。
6. 本轮角色口径固定为“Atlas 当前会话直修 / 主导实现”；回测 Agent 不得把补写 prompt / handoff 误记为已取得业务 Token 的独立实施。
7. P-LOG 区无需文件级 Token，但仍必须遵守角色独占写权限。

## 当前状态

- 预审状态：已通过
- 批次 A Token 状态：✅ locked (tok-6739689c)
- 批次 B Token 状态：✅ locked (tok-7bb948e5)
- 批次 C Token 状态：✅ locked (tok-33baea65)
- 批次 D Token 状态：✅ locked (tok-5ec15b54)
- 解锁时间：3 天执行窗口内
- 失效时间：已锁回
- 锁回时间：2026-04-10
- lockback 结果：A~D 四批全部锁回

## 操作日志

| 时间 | 操作 | 备注 |
|------|------|------|
| 2026-04-08 | 预审建档完成 | 白名单冻结 |
| 2026-04-09 | 3 天执行窗口启动 | Jay.S 确认 |
| 2026-04-10 | A~D 四批 Token 签发+实施+lockback | 全部 locked |
| 2026-04-10 | Air 代码同步 + 容器重启 | rsync + docker restart |
| 2026-04-10 | 远端验证通过 | 8103 API + 3001 Web + MD5 一致 |

## 结论

**TASK-0008 A~D 四批全部实施完成并锁回。Air 端代码已同步并通过验证。Phase E 全闭环，回测进入维护态。**

---

【签名】Atlas
【时间】2026-04-10
【设备】MacBook