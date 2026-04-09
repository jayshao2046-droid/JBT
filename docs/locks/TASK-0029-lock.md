# TASK-0029 Lock 记录

## Lock 信息

- 任务 ID：TASK-0029
- 阶段：极速维修 V2 正式制度修订已完成并锁回
- 当前任务是否仍处于“预审未执行”状态：否（两份 P0 治理文件已落盘）
- 当前总状态：`locked`
- 执行 Agent：
  - 项目架构师（本轮正式制度修订与账本同步）
  - 后续单服务 owner agent（仅在具体单服务 P1 维修任务中按 V2 规则执行）

## 本轮 P0 Token 留痕

1. token_id：`tok-8dd6775d-4335-48c8-a545-854344a2158f`
2. review-id：`REVIEW-TASK-0029`
3. P0 白名单：
   - `WORKFLOW.md`
   - `.github/instructions/change-control.instructions.md`
4. 锁回结果：已完成 validate，并执行 approved lockback。
5. lockback_summary：`TASK-0029 正式制度修订完成，自校验通过，执行锁回`
6. 当前状态：`locked`

## 本轮 P-LOG 同步文件

1. `docs/reviews/TASK-0029-review.md`
2. `docs/locks/TASK-0029-lock.md`
3. `docs/handoffs/TASK-0029-架构预审交接单.md`
4. `docs/prompts/公共项目提示词.md`
5. `docs/prompts/agents/项目架构师提示词.md`

## 当前制度状态声明

1. `WORKFLOW.md` 与 `.github/instructions/change-control.instructions.md` 已执行正式制度修订并完成锁回。
2. `极速维修 V2` 正式治理规则已落地并锁回，但仍仅限**标准流程之外的单服务 P1 极速通道**。
3. “维修区域认证 + Hotfix Token” 的治理语义已正式落盘；在当前工具能力下，Hotfix Token 仍必须落成最小文件白名单，不代表目录级通配解锁。
4. 用户未确认成功前，不补全后置材料、不锁回、不独立提交；失败继续在原任务内返工维修。
5. 两份 P0 治理文件当前均已重新锁定；本轮锁回留痕统一收口为：token_id `tok-8dd6775d-4335-48c8-a545-854344a2158f`，review-id `REVIEW-TASK-0029`，lockback_summary `TASK-0029 正式制度修订完成，自校验通过，执行锁回`，状态 `locked`。

## 正式适用边界

1. 正式适用范围：单服务 P1 热修 / 投诉 / 生产维修。
2. 正式流程：`只读确认 -> 1 分钟内完成最小维修单 / 维修区域认证 / Hotfix Token -> 最小自校验 -> 项目架构师快速验证 -> 先交付用户 -> 用户确认后一次性补材料 / 锁回 / 独立提交`。
3. 只要涉及跨服务、`shared/contracts/**`、任一 P0 文件、目录变化、`shared/python-common/**`、`docker-compose.dev.yml`、任一 `.env.example`、`runtime/**`、`logs/**` 或任一真实 `.env`，必须立即退出 V2，回到标准流程。

## 当前继续锁定范围

1. `WORKFLOW.md`
2. `.github/**`
3. `shared/contracts/**`
4. `services/**`
5. `docker-compose.dev.yml`
6. 任一服务 `.env.example`
7. `runtime/**`
8. `logs/**`
9. 任一真实 `.env`
10. 其他全部非白名单文件

## 结论

`TASK-0029` 当前已完成正式制度修订并锁回；制度文本已正式落地，两份 P0 治理文件已重新锁定，相关 P-LOG 同步完成。当前锁控留痕为：token_id `tok-8dd6775d-4335-48c8-a545-854344a2158f`，review-id `REVIEW-TASK-0029`，lockback_summary `TASK-0029 正式制度修订完成，自校验通过，执行锁回`，状态 `locked`。