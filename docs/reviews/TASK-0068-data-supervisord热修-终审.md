# TASK-0068 终审记录 — data supervisord 路径热修

【签名】Atlas（U0 事后审计）
【时间】2026-04-12 15:10
【设备】MacBook
【Token】tok-9b4b3379-0cc5-4c81-87b9-f6426f6508a8
【TTL】120 分钟
【模式】U0 — 单服务应急维修，事后审计

---

## 问题描述

jbt-data 容器（Mini:8105）三个 supervisord 进程全部 FATAL：
- `jbt-data-api`：`ModuleNotFoundError: No module named 'services.data.src'`
- `jbt-data-scheduler`：同上
- `jbt-data-health`：每秒重启（ModuleNotFoundError）

外部访问 http://192.168.31.156:8105/health 返回 200 是 healthcheck 误报（false positive）。

## 根因

`services/data/docker-compose.dev.yml` volume mount 配置：
```yaml
volumes:
  - ./services/data:/app
```
容器内 `/app/` 实际为 Mini 上 `services/data/` 目录，代码在 `/app/src/`。

但 `services/data/supervisord.conf` 使用 `python -m services.data.src.main`（错误路径），应为 `python -m src.main`。

35个 Python 文件内部导入也使用 `from services.data.src.*`，全部需要改为 `from src.*`。

## 修复范围（U0 最小必要）

**services/data/supervisord.conf**：3 处命令路径修正
- `services.data.src.main` → `src.main`
- `services.data.src.scheduler.data_scheduler` → `src.scheduler.data_scheduler`
- `services.data.src.health.health_check` → `src.health.health_check`

**35个 Python 文件导入路径重构**（批量 sed）：
`from services.data.src.*` → `from src.*`
`import services.data.src.*` → `import src.*`

额外修复（heartbeat.py, data_scheduler.py）：4 处代码内残余旧路径

## 执行结果

**Git commit**: `9021afa`
**执行方**: Claude-Code
**三地状态**: MacBook ✅ / Studio 9021afa ✅ / Mini rsync ✅

## 验收证据

```
# Atlas 独立验收（2026-04-12 15:08）
$ curl -s http://192.168.31.156:8105/health
{"status":"ok","service":"jbt-data","version":"1.0.0"}

$ ssh jaybot@192.168.31.156 "/usr/local/bin/docker exec JBT-DATA-8105 supervisorctl status"
jbt-data-api        RUNNING   pid 7, uptime 0:02:10  ✅
jbt-data-health     EXITED    Apr 12 02:52 PM        ✅（一次性任务，exit 0，正常）
jbt-data-scheduler  RUNNING   pid 9, uptime 0:02:10  ✅
```

healthcheck 状态：`healthy`（从 false positive 变为真健康）✅

## U0 约束核查

- [x] 单服务（services/data/）边界，未触及跨服务
- [x] 未触及 P0 保护区（无 shared/contracts, .github, docker-compose.dev.yml 等）
- [x] 用户（Jay.S）确认成功后补齐材料
- [x] 最小文件范围（supervisord.conf + 35个src/*.py）
- [x] 事后审计口径：先修复验收，后补材料

## 终审结论

✅ **通过**。根因清晰、修复最小、验收证据完整。jbt-data 服务从假健康变为真健康运行。
