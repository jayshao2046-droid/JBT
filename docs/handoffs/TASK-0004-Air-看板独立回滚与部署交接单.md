# TASK-0004 Air 看板独立回滚与部署交接单

【签名】Atlas
【时间】2026-04-06 当前会话
【设备】MacBook

## Handoff 信息

- 任务 ID：TASK-0004
- 来源 Agent：Atlas
- 目标角色：Jay.S、项目架构师、回测 Agent
- 当前状态：Air 看板单服务部署与 API 500 修复均已完成；JBT 已正式推送到 GitHub origin
- 当前交付基线：`5690c74`（`feat(backtest): finalize TASK-0008 fixes and docker prep`）

## 本次冻结口径

1. Air 上回测后端与看板前端采用两服务拆分：`backtest`（8103）与 `backtest-web`（3001）。
2. 本轮部署只允许对 `backtest-web` 单服务做 build / up / rollback；后端 `backtest` 不得被顺手重建。
3. 看板独立回滚依赖运行态镜像快照，不走全局 reset，也不走整仓整体回退。
4. 本轮本地仓库已完成 git 提交，当前工作区干净，可直接 push。

## 实际执行结果

1. 本地文档补录已提交为 `fb65f5f`：`docs(backtest): record Air dashboard rollback handoff`。
2. 已将 JBT 的 `origin` 正式切到 GitHub 仓库 `https://github.com/jayshao2046-droid/JBT.git`，并完成 `main` 首次推送；本地 bare 仓库保留为 `local` 备份 remote。
3. 代码已通过 rsync 同步到 Air：`~/botquant-backtest-prod/`。
4. Air 上旧看板容器实际名称为 `backtest-dashboard`，状态为 `Up 35 hours (unhealthy)`，并占用 3001 端口。
5. 已先为旧容器生成回滚镜像：`jbt-backtest-web:rollback-202604060256`。
6. 已移除旧 `backtest-dashboard` 与失败创建的 `JBT-BACKTEST-WEB-3001`，随后重新执行 `docker compose -f docker-compose.dev.yml up -d --no-deps backtest-web`。
7. 新容器 `JBT-BACKTEST-WEB-3001` 已启动成功，`curl -I http://127.0.0.1:3001` 返回 `HTTP/1.1 200 OK`。
8. Air 上后端容器 `backtest-api` 保持 `Up 35 hours (healthy)`，本轮未被重建或重启。
9. 后续远端看板出现 API 500，经核对并非后端宕机，而是 `JBT-BACKTEST-WEB-3001` 位于 `botquant-backtest-prod_default`，`backtest-api` 位于 `backtest_backtest-net`，且看板容器内 `BACKEND_BASE_URL=http://backtest:8103` 无法解析到现网后端。
10. 已执行 `docker network connect --alias backtest botquant-backtest-prod_default backtest-api`，把现网后端补接到看板网络并增加 `backtest` 别名；修复后 `curl http://127.0.0.1:3001/api/strategies` 返回 `HTTP/1.1 200 OK`，远端 500 已消失。

## Air 部署前检查项

1. Air 项目目录统一为 `~/botquant-backtest-prod/`。
2. Air 上需已有 `.env` 或等价环境变量，至少保证 `TQSDK_AUTH_USERNAME`、`TQSDK_AUTH_PASSWORD`、`JBT_JWT_SECRET` 已配置。
3. Air 上当前 compose 网络与 `JBT-BACKTEST-8103` 后端容器保持可用，`backtest-web` 只通过 `http://backtest:8103` 访问后端。

## 建议执行命令

### 一、本地 push

1. `cd /Users/jayshao/JBT && git push origin main`

### 二、同步到 Air

1. `rsync -av --delete --exclude '.git' --exclude '.venv' --exclude 'node_modules' --exclude '.next' /Users/jayshao/JBT/ air:~/botquant-backtest-prod/`

### 三、Air 上部署看板

1. `ssh air 'cd ~/botquant-backtest-prod && docker commit JBT-BACKTEST-WEB-3001 jbt-backtest-web:rollback-$(date +%Y%m%d%H%M) || true'`
2. `ssh air 'cd ~/botquant-backtest-prod && docker compose build backtest-web'`
3. `ssh air 'cd ~/botquant-backtest-prod && docker compose up -d --no-deps backtest-web'`
4. `ssh air 'curl -I http://127.0.0.1:3001'`

## Air 独立回滚命令

1. `ssh air 'docker stop JBT-BACKTEST-WEB-3001 && docker rm JBT-BACKTEST-WEB-3001'`
2. `ssh air 'docker images --format "{{.Repository}}:{{.Tag}}" | grep "^jbt-backtest-web:rollback-" | head -n 1'`
3. `ssh air 'docker run -d --name JBT-BACKTEST-WEB-3001 --restart unless-stopped -p 3001:3001 --network botquant-backtest-prod_default -e BACKEND_BASE_URL=http://backtest:8103 <ROLLBACK_TAG>'`
4. `ssh air 'curl -I http://127.0.0.1:3001'`

## 说明

1. 第三步中的 `botquant-backtest-prod_default` 为当前建议 compose 网络名；若 Air 实际网络名不同，应以 Air 上现网网络名替换。
2. 回滚只恢复 `JBT-BACKTEST-WEB-3001`，不得停止或重建 `JBT-BACKTEST-8103`。
3. 若 Air 当前尚无 `JBT-BACKTEST-WEB-3001`，则第一条快照命令允许失败并继续。
4. 本轮实际回滚基线已更新为 `jbt-backtest-web:rollback-202604060256`。

## 向 Jay.S 汇报摘要

1. 现在 Air 上已经切换到新的 `JBT-BACKTEST-WEB-3001`，3001 返回 200，8103 后端保持健康未动。
2. 当前可用回滚点是 `jbt-backtest-web:rollback-202604060256`，真回滚时只恢复看板容器，不会把后端一起带回去。
3. JBT 代码已经正式推送到 GitHub origin；当前仓内 `origin` 指向 GitHub，`local` 保留本地备份 remote。
