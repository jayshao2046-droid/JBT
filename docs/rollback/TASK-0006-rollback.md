# TASK-0006 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0006
- 执行 Agent：
  - 项目架构师（预审治理）
  - 回测 Agent（业务文件执行主体；以 Jay.S 最终签发 Token 绑定主体为准）
- 对应提交 ID：待任务完成后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`（不得使用 `git reset --hard`）
- 回滚结果：N/A

## 影响文件（治理阶段，已写入）

1. `docs/tasks/TASK-0006-backtest-Docker部署与契约更新.md`
2. `docs/reviews/TASK-0006-review.md`
3. `docs/locks/TASK-0006-lock.md`
4. `docs/rollback/TASK-0006-rollback.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 影响文件（业务执行阶段，待 Token 后）

### P1 区（3 文件，新建）
1. `services/backtest/Dockerfile`
2. `services/backtest/V0-backtext 看板/Dockerfile`
3. `services/backtest/docker-compose.yml`

### P0 区（1 文件，修改）
4. `shared/contracts/backtest/api.md`

## 回滚原则

1. 当前阶段尚未产生业务代码写入，因此暂无实际回滚动作。
2. 未来如执行业务文件，回滚粒度必须绑定 TASK-0006 对应提交，不得使用全局回退替代。
3. `docker-compose.dev.yml`、`services/backtest/.env.example`、TASK-0005 已锁回的业务文件不纳入本任务的回滚范围。
4. 不得使用 `git reset --hard`；历史必须保留，默认仅允许对 TASK-0006 对应提交执行定向 `git revert`。
5. 若 `shared/contracts/backtest/api.md` 回滚，必须确认 `backtest_job.md` 中的 `strategy_template_id` 描述同步匹配，不引入契约不一致。
6. 远端 192.168.31.245 上的 Docker 容器若需回滚，执行 `docker-compose down`，并在回滚提交后重新 `docker-compose up -d`；不得直接删除镜像，保留回滚前的镜像备份。

## 当前结论

- 预审账本已建立。
- 当前无业务代码提交需要回滚。
- 后续进入业务执行阶段时，必须继续保持"单任务、单批次、单提交、定向回滚"的治理边界。
