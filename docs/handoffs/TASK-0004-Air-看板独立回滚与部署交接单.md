# TASK-0004 Air 看板独立回滚与部署交接单

【签名】Atlas
【时间】2026-04-06 当前会话
【设备】MacBook

## Handoff 信息

- 任务 ID：TASK-0004
- 来源 Agent：Atlas
- 目标角色：Jay.S、项目架构师、回测 Agent
- 当前状态：已完成本地提交，待 Jay.S 确认后执行 push 与 Air 部署命令
- 当前交付基线：`5690c74`（`feat(backtest): finalize TASK-0008 fixes and docker prep`）

## 本次冻结口径

1. Air 上回测后端与看板前端采用两服务拆分：`backtest`（8103）与 `backtest-web`（3001）。
2. 本轮部署只允许对 `backtest-web` 单服务做 build / up / rollback；后端 `backtest` 不得被顺手重建。
3. 看板独立回滚依赖运行态镜像快照，不走全局 reset，也不走整仓整体回退。
4. 本轮本地仓库已完成 git 提交，当前工作区干净，可直接 push。

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

## 向 Jay.S 汇报摘要

1. 现在仓内已经具备看板端单服务部署前提，Air 上可以只发 `backtest-web`，不用动 8103 后端。
2. 我已经把 push、同步、部署和回滚命令全部整理出来；你确认后我就按这套命令执行。
3. 真正回滚时只回 `JBT-BACKTEST-WEB-3001`，不会把后端一起带回去。
