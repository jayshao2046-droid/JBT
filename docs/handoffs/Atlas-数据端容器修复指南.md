# Atlas → Claude-Code: 数据端容器修复指南

> 签发时间: 2026-04-13  
> 签发人: Atlas (总项目经理)  
> 目标: Mini (192.168.31.74) 上的 JBT-DATA-8105 容器完全修复  
> 优先级: P0（明天周一开盘前必须修复）

---

## 一、当前状态总结

| 项目 | 状态 | 说明 |
|------|------|------|
| 数据迁移 | ✅ 已完成 | Atlas 已将 `~/jbt-data/` 全部 2.3GB (42006 parquets, 5368 目录) 复制到容器 `/data/` |
| API (jbt-data-api) | ✅ RUNNING | 端口 8105，健康检查通过 |
| Scheduler | ⚠️ RUNNING 但空转 | 进程活着，但所有任务因缺包全部失败 |
| Health Monitor | ❌ EXITED | 非守护进程，已退出 |
| Legacy daemon | ⚠️ PID 21737 运行中 | 宿主机上的旧进程仍在运行，部分补偿采集 |

---

## 二、根因分析（5个问题）

### 问题 1：主 bind mount 缺失（最关键）

容器启动时丢失了 `docker-compose.dev.yml` 定义的主要 bind mount：

```yaml
# docker-compose.dev.yml 定义了3个卷
volumes:
  - ./services/data:/app             # <-- 这个完全缺失！
  - jbt-data-storage:/data
  - ./services/data/configs:/app/services/data/configs:ro
```

**实际容器只有 2 个挂载**：
- `jbt_jbt-data-storage` → `/data` (named volume)  
- `bind: ~/jbt/services/data/configs` → `/app/services/data/configs`

**后果**: 容器运行在过时的 Docker image layer 上，不追踪宿主代码变更。`/app/` 目录只有 Dockerfile COPY 的旧文件。

**修复**: 使用完整的 compose 命令重建：
```bash
cd ~/JBT && docker compose -f docker-compose.dev.yml up -d --build jbt-data
```

如果 Mini 上有 `docker-compose.mac.override.yml`，也需要加上 `-f docker-compose.mac.override.yml`。

### 问题 2：requirements.txt 缺少关键依赖

**容器内 `/app/requirements.txt`（构建时快照）**只有 10 个包，缺少：
- `pyarrow>=10.0.0` — parquet 读写必需
- `apscheduler>=3.10.0` — 定时调度必需  
- `akshare>=1.18.0` — A 股/期货/宏观数据采集必需

**宿主 `services/data/requirements.txt` 已包含 pyarrow 和 apscheduler**，但仍缺 `akshare`。

需要新增到 `services/data/requirements.txt`：
```
akshare>=1.18.0
lxml>=4.9.0
beautifulsoup4>=4.12.0
```

> 注意：akshare 依赖较重（lxml, bs4, requests, tqdm 等），安装时间较长。

### 问题 3：supervisord.conf PYTHONPATH 不一致

当前配置：
```ini
environment=PYTHONPATH="/app/services/data"
directory=/app/services/data
command=python -m src.scheduler.data_scheduler
```

- **如果 bind mount 恢复** (`./services/data:/app`): 代码在 `/app/src/`  
  → 改为 `PYTHONPATH="/app"`, `directory=/app`
  
- **如果不用 bind mount** (纯 image): 代码在 `/app/services/data/src/`（Dockerfile COPY 路径）  
  → 当前的 `PYTHONPATH="/app/services/data"`, `directory=/app/services/data"` 是正确的

**建议统一方案**：恢复 bind mount + 修改 supervisord.conf 为：
```ini
[program:jbt-data-api]
directory=/app
environment=PYTHONPATH="/app",DATA_STORAGE_ROOT="/data",JBT_DATA_LOG_DIR="/data/logs"

[program:jbt-data-scheduler]
directory=/app
environment=PYTHONPATH="/app",DATA_STORAGE_ROOT="/data",JBT_DATA_LOG_DIR="/data/logs"

[program:jbt-data-health]
directory=/app
environment=PYTHONPATH="/app",DATA_STORAGE_ROOT="/data",JBT_DATA_LOG_DIR="/data/logs"
```

### 问题 4：数据卷策略需要改进

当前使用 Docker named volume `jbt-data-storage` 挂载到 `/data`。存在的问题：
- Named volume 初始为空，需要手动迁移数据（Atlas 已完成一次）
- 宿主 legacy daemon 写入 `~/jbt-data/`，容器写入 `/data/`，数据不同步
- 每次重建容器，named volume 保留但可能与宿主数据脱节

**推荐方案（长期）**：如果 `docker-compose.dev.yml` 可以修改，将 named volume 改为 bind mount：
```yaml
volumes:
  - ./services/data:/app
  - /Users/jaybot/jbt-data:/data
  - ./services/data/configs:/app/services/data/configs:ro
```
然后删除底部的 `jbt-data-storage:` volume 定义。

> ⚠️ docker-compose.dev.yml 是 P0 保护文件，修改需要走标准流程（预审 + Token）。

### 问题 5：NAS 备份脚本缺失

Scheduler 日志报错：
```
bash: /app/services/data/src/scripts/nas_backup.sh: No such file or directory
```
如果暂不需要 NAS 备份，可在 scheduler 代码中临时禁用该任务。

---

## 三、修复优先级排序

1. **P0**: 补全 requirements.txt（加入 akshare + pyarrow + apscheduler + 依赖）
2. **P0**: 修改 supervisord.conf 统一 PYTHONPATH（配合 bind mount 或 image 方案二选一）
3. **P0**: 重建容器（`docker compose up -d --build jbt-data`），确保 bind mount 正确挂载
4. **P1**: 验证 scheduler 全部任务可正常执行（特别是 news_api、stock_minute、sentiment）
5. **P2**: 处理数据卷策略（named volume → bind mount，需要改 compose 文件）
6. **P2**: 停止 legacy daemon（PID 21737），确认容器 scheduler 完全接管后再停

---

## 四、关键文件与路径

| 文件 | 宿主路径 | 容器路径 | 说明 |
|------|---------|---------|------|
| requirements.txt | `services/data/requirements.txt` | `/app/requirements.txt` (bind mount后) | 需修改 |
| supervisord.conf | `services/data/supervisord.conf` | `/etc/supervisor/conf.d/jbt-data.conf` (COPY) | 需修改 |
| Dockerfile | `services/data/Dockerfile` | - | ENV PYTHONPATH=/app (正确) |
| docker-compose | `docker-compose.dev.yml` | - | P0 保护，需 Token |
| 数据根目录 | `~/jbt-data/` | `/data/` | 已迁移 |
| Scheduler 日志 | - | `/data/logs/scheduler_stderr.log` | 查看错误 |

---

## 五、容器内 Python 包清单（当前 vs 需要）

**当前已安装**: fastapi, uvicorn, pandas, polars, httpx, pydantic, psutil, pyyaml  
**缺失但必需**: pyarrow, apscheduler, akshare, lxml, beautifulsoup4, aiohttp  
**宿主 legacy daemon**: Python 3.9, akshare 1.18.35 (工作正常)

---

## 六、验证清单

修复完成后，请逐项验证：

- [ ] `docker exec JBT-DATA-8105 pip show pyarrow apscheduler akshare` 均有输出
- [ ] `docker exec JBT-DATA-8105 supervisorctl status` — 三个进程 RUNNING
- [ ] `docker exec JBT-DATA-8105 ls /app/src/` 可看到完整目录结构（bind mount 生效）
- [ ] `curl http://localhost:8105/health` 返回 ok
- [ ] `docker exec JBT-DATA-8105 tail -5 /data/logs/scheduler_stderr.log` 无 ModuleNotFoundError
- [ ] `docker exec JBT-DATA-8105 find /data/ -name "*.parquet" | wc -l` ≥ 42006
- [ ] News collection 能新增数据（等待下一个定时窗口或手动触发）

---

## 七、数据完整性快照（Atlas 已验证）

| 数据类型 | 文件数/大小 | 最新更新 |
|---------|------------|---------|
| stock_minute (parquet) | 15,647 | 5日内 |
| futures daily/1min | 937 + 95 | 5日内 |
| news_collected (json) | 34MB | 4/9 |
| news_api/news_rss | parquet | 4/13 (legacy daemon) |
| sentiment | 10MB | 4/13 (legacy daemon) |
| macro_global | 目录存在 | 3月底 |
| 总 parquet 数 | 42,006 | - |
| 总数据量 | 2.3GB | - |

所有数据均已复制到容器 `/data/` volume 内。
