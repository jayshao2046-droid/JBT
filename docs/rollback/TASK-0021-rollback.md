# TASK-0021 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0021
- 执行 Agent：
  - 项目架构师（当前预审）
  - Atlas（当前治理留痕）
  - 决策 Agent（未来实施主体）
- 对应提交 ID：待后续任务提交后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`，不得使用 `git reset --hard`
- 回滚结果：当前无业务代码执行，无需代码回滚

## 影响文件（当前治理阶段）

1. `docs/tasks/TASK-0021-decision-旧决策域清洗升级迁移预审.md`
2. `docs/reviews/TASK-0021-review.md`
3. `docs/locks/TASK-0021-lock.md`
4. `docs/rollback/TASK-0021-rollback.md`
5. `docs/handoffs/TASK-0021-旧决策域清洗升级迁移预审交接单.md`
6. `docs/prompts/总项目经理调度提示词.md`
7. `docs/prompts/agents/总项目经理提示词.md`

## 当前轮次回滚结论

1. 当前轮次只发生治理账本与 Atlas 调度留痕写入，尚未发生 `services/**`、`shared/contracts/**` 或 `integrations/**` 代码执行。
2. 当前不存在需要对 decision 服务、决策看板、契约、通知体系或 legacy 适配执行的回滚动作。
3. 若需要撤销本轮，只允许对治理账本提交执行定向 `git revert`。

## 未来进入执行后的回滚粒度

1. 批次 A `shared/contracts/**` 必须作为独立 P0 提交、独立 revert。
2. 批次 B `integrations/legacy-botquant/**` 必须作为独立 P0 提交、独立 revert。
3. 批次 C `services/decision/**` 核心服务必须作为独立 P1 批次、独立提交、独立 revert。
4. 批次 D `services/decision/**` 研究能力与门禁联动必须作为独立 P1 批次、独立提交、独立 revert。
5. 批次 E `services/dashboard/**` 决策看板必须作为独立 P1 批次、独立提交、独立 revert。
6. 批次 F 决策通知体系必须作为独立 P1 批次、独立提交、独立 revert。
7. 任何 `.env.example` 变更必须作为独立 P0 提交，不得与业务实现混回滚。

## Secret / 运行时配置回滚要求

1. 真实模型 key、飞书 webhook、邮件 Secret 不得入库；回滚只处理占位说明，不处理真实 Secret。
2. 若未来存在部署侧 env mapping / fallback，只允许回滚映射说明与消费逻辑，不得把真实 Secret 写回 Git。
3. legacy 路径只能作为只读迁移参考，不得把外部 `.env` 或凭证路径耦合进仓内实现。

## 当前结论

1. 当前轮次尚未发生代码执行。
2. 当前无服务提交需要回滚。
3. 后续如进入实施，必须保持各批次独立提交、独立回滚。 