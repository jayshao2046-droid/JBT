# TASK-0004 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0004
- 执行 Agent：
  - 项目架构师（预审治理）
  - 回测 Agent（页面实现）
  - Atlas（Air 部署与运行态回滚执行）
- 对应提交 ID：`5690c74`（2026-04-06 当前交付基线）
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：代码层定向 `git revert` + Air 运行态仅回滚 `backtest-web` 单服务
- 回滚结果：N/A

## 影响文件（治理阶段）

1. `docs/tasks/TASK-0004-backtest-dashboard-Phase1-两页收敛.md`
2. `docs/reviews/TASK-0004-review.md`
3. `docs/locks/TASK-0004-lock.md`
4. `docs/rollback/TASK-0004-rollback.md`
5. `docs/handoffs/TASK-0004-看板预审交接单.md`
6. `docs/handoffs/TASK-0004-Air-看板独立回滚与部署交接单.md`
7. 对应执行 Agent 的私有 prompt

## 影响文件（开发阶段）

1. `services/backtest/backtest_web/app/agent-network/page.tsx`
2. `services/backtest/backtest_web/app/operations/page.tsx`
3. `services/backtest/backtest_web/src/utils/api.ts`
4. `services/backtest/backtest_web/src/utils/strategyPresentation.ts`
5. `services/backtest/backtest_web/Dockerfile`
6. `docker-compose.dev.yml` 中 `backtest-web` 服务定义（运行态独立部署前提）

## 独立回滚前提

1. 根级 `docker-compose.dev.yml` 已将回测后端 `backtest` 与看板前端 `backtest-web` 拆为两个独立服务。
2. Air 上看板容器名冻结为 `JBT-BACKTEST-WEB-3001`，后端容器名冻结为 `JBT-BACKTEST-8103`。
3. 看板端部署、重启、验证、回滚都只允许操作 `backtest-web`，不得顺带重建 `backtest`。
4. 看板端回滚前必须先在 Air 为当前运行中的 `JBT-BACKTEST-WEB-3001` 做镜像快照，作为单服务回滚点。

## 代码回滚原则

1. 治理文件与业务文件应随各自独立提交分别回滚，不得混用一次全局回退。
2. 若后续再有纯看板提交，必须保持独立提交，回滚时只允许对看板提交执行定向 `git revert`。
3. 不得顺带恢复 `app/layout.tsx`、`package.json`、回测引擎文件或本轮未纳入看板范围的其他页面文件。
4. 若后续发生补充预审扩白名单，必须在本文件追加新的影响文件与对应回滚边界。

## Air 运行态独立回滚步骤

1. 部署前先为当前看板容器制作单服务快照：`docker commit JBT-BACKTEST-WEB-3001 jbt-backtest-web:rollback-<YYYYMMDDHHMM>`。
2. 记录快照 tag 到 `docs/handoffs/TASK-0004-Air-看板独立回滚与部署交接单.md`。
3. 如新版本看板回滚，只停止并移除 `JBT-BACKTEST-WEB-3001`，不得触碰 `JBT-BACKTEST-8103`。
4. 使用上一步快照 tag 重建 `JBT-BACKTEST-WEB-3001`，并保持 `BACKEND_BASE_URL=http://backtest:8103` 与原 compose 网络不变。
5. 回滚后只验证 3001 看板可访问、API 仍指向 8103、回测详情页与策略管理页加载正常。

## 当前结论

- TASK-0004 当前部署基线已固定到提交 `5690c74`。
- 看板端独立回滚口径已冻结为“Air 上只回滚 `backtest-web` 单服务，不触碰 `backtest` 后端容器”。
- push 与 Air 部署命令待 Jay.S 确认后由 Atlas 执行。
