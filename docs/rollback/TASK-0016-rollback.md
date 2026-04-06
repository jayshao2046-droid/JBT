# TASK-0016 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0016
- 执行 Agent：
  - 项目架构师（当前治理补录）
  - 模拟交易 Agent（未来服务侧实现）
  - Jay.S 指定的集成执行主体（未来 `integrations/**` 批次）
- 对应提交 ID：待后续任务提交后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`，不得使用 `git reset --hard`
- 回滚结果：当前无业务代码执行，无需代码回滚

## 影响文件（当前治理阶段）

1. `docs/tasks/TASK-0016-J_BotQuant-Studio-决策端API接入预审.md`
2. `docs/reviews/TASK-0016-review.md`
3. `docs/locks/TASK-0016-lock.md`
4. `docs/rollback/TASK-0016-rollback.md`
5. `docs/handoffs/TASK-0016-Studio-正式接入预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前轮次回滚结论

1. 当前轮次只发生治理账本写入，尚未发生 `shared/contracts/**`、`services/sim-trading/**` 或 `integrations/legacy-botquant/**` 的代码执行。
2. 当前不存在需要对正式接入实现、兼容层或远端环境执行的回滚动作。
3. 若需要撤销本轮，只允许对治理账本提交执行定向 `git revert`。

## 未来进入执行后的回滚粒度

1. 正式 API 契约若变更到 `shared/contracts/**`，必须作为独立 P0 批次、独立提交、独立 revert。
2. `services/sim-trading/**` 的正式接入入口、校验逻辑或只读状态接口必须作为独立 P1 批次、独立提交、独立 revert。
3. `integrations/legacy-botquant/**` 的外部适配逻辑必须作为独立 P0 批次、独立提交、独立 revert。
4. 若实际执行中出现新批次或新文件，必须追加更新本文件，不能让 contracts、服务代码与 integrations 混在一次回滚中。

## Secret / 远端环境 / compose / integrations 回滚要求

1. 上游 API URL、鉴权 key、签名密钥与回调凭证不得入库；回滚只处理占位说明与接入文档，不处理真实 Secret。
2. `integrations/**` 的任何实现回滚必须保持独立，不得借回滚服务侧代码顺手回退兼容层。
3. 本任务未来不应触碰 `docker-compose.dev.yml` 或远端部署动作；若正式接入需要部署调整，应交由 `TASK-0017` 单独管理。

## 当前结论

1. 当前轮次尚未发生代码执行。
2. 当前无 contracts、服务代码或 integrations 提交需要回滚。
3. 后续如进入实施，必须保持 contracts、服务侧与 integrations 三条路径可独立回滚。