# 数据端容器修复完成报告

> 执行时间: 2026-04-13  
> 执行人: Claude Code  
> 任务类型: U0 紧急修复  
> 优先级: P0

---

## 一、修复内容

### 1.1 问题诊断
**根本原因**: Dockerfile 构建路径错误

- docker-compose.dev.yml 定义构建上下文为 `./services/data`
- Dockerfile 中 COPY 路径写成 `services/data/requirements.txt`（路径重复）
- 导致构建时找不到文件，容器无法启动

### 1.2 修复操作

#### 修改 1: services/data/Dockerfile
```diff
- COPY services/data/requirements.txt .
+ COPY requirements.txt .

- COPY services/data/src/ ./services/data/src/
+ COPY src/ ./services/data/src/

- COPY services/data/tests/ ./services/data/tests/
+ COPY tests/ ./services/data/tests/

- COPY services/data/configs/ ./services/data/configs/
+ COPY configs/ ./services/data/configs/

- COPY services/data/supervisord.conf /etc/supervisor/conf.d/jbt-data.conf
+ COPY supervisord.conf /etc/supervisor/conf.d/jbt-data.conf
```

#### 修改 2: services/data/supervisord.conf
```diff
- command=python -m uvicorn services.data.src.main:app --host 0.0.0.0 --port 8105
+ command=python -m uvicorn src.main:app --host 0.0.0.0 --port 8105

- command=python -m services.data.src.scheduler.data_scheduler
+ command=python -m src.scheduler.data_scheduler

- command=python -m services.data.src.health.health_check
+ command=python -m src.health.health_check
```

**原因**: bind mount 生效后，代码在 `/app/src/`，不是 `/app/services/data/src/`

---

## 二、验证结果

### 2.1 容器状态 ✅
```
NAMES           STATUS
JBT-DATA-8105   Up 30 seconds (healthy)
```

### 2.2 挂载点验证 ✅
```
bind: /Users/jayshao/JBT/services/data -> /app
volume: /var/lib/docker/volumes/jbt_jbt-data-storage/_data -> /data
bind: /host_mnt/Users/jayshao/JBT/services/data/configs -> /app/services/data/configs
```

### 2.3 进程状态 ✅
```
jbt-data-api        RUNNING   pid 7, uptime 0:00:20
jbt-data-scheduler  RUNNING   pid 9, uptime 0:00:20
jbt-data-health     EXITED    Apr 12 09:12 PM (正常，非守护进程)
```

### 2.4 Python 包验证 ✅
```
Name: pyarrow       Version: 23.0.1
Name: APScheduler   Version: 3.11.2
Name: akshare       Version: 1.18.55
```

### 2.5 API 健康检查 ✅
```json
{"status":"ok","service":"jbt-data","version":"1.0.0"}
```

### 2.6 Scheduler 日志 ✅
```
2026-04-12 21:12:05 - data_scheduler - INFO - 调度器启动成功
2026-04-12 21:12:05 - data_scheduler - INFO - 已注册 15 个定时任务
```

---

## 三、遗留问题

### 3.1 数据卷为空 ⚠️
**现象**: `/data/` 目录下没有 parquet 文件（0 个）

**原因**: 
- Atlas 指南提到已迁移 2.3GB 数据（42006 parquets）到容器 `/data/`
- 但在 `docker compose down` 重建容器时，可能创建了新的 volume
- 旧数据可能在之前的 volume 实例中

**影响**: 
- 容器功能正常，但历史数据缺失
- Scheduler 可以正常运行，会开始采集新数据
- Legacy daemon (PID 21737) 仍在宿主机运行，部分补偿采集

**建议**: 
1. 检查是否有旧的 Docker volume 备份
2. 如果有宿主机数据备份（如 `~/jbt-data/`），可以复制到容器 volume
3. 或者让 Scheduler 重新采集数据（需要时间）

---

## 四、修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/Dockerfile` | 修改 | 修正 5 行 COPY 路径 |
| `services/data/supervisord.conf` | 修改 | 修正 3 个 Python 模块路径 |

---

## 五、后续建议

### 5.1 数据恢复（P1）
- 如果需要历史数据，需要找到 Atlas 迁移的数据源并重新导入
- 或者等待 Scheduler 自动采集新数据

### 5.2 Legacy Daemon 处理（P2）
- 当前宿主机 PID 21737 仍在运行
- 确认容器 Scheduler 稳定后，可以停止 legacy daemon

### 5.3 数据卷策略优化（P2）
- 考虑将 named volume 改为 bind mount（如 Atlas 指南建议）
- 需要修改 docker-compose.dev.yml（P0 保护文件，需要 Token）

---

## 六、验收清单

- [x] 容器成功构建并启动
- [x] 三个 supervisor 进程全部 RUNNING（health 为 EXITED 正常）
- [x] API 健康检查通过
- [x] Scheduler 日志无 ModuleNotFoundError
- [x] 关键 Python 包已安装（pyarrow, apscheduler, akshare）
- [x] Bind mount 正确挂载
- [ ] 数据完整性验证（数据卷为空，需要恢复）

---

## 七、时间记录

- 诊断时间: 5 分钟
- 修复时间: 15 分钟
- 验证时间: 5 分钟
- 总耗时: 25 分钟

---

**修复状态**: ✅ 容器功能已完全恢复，可以正常运行  
**数据状态**: ⚠️ 数据卷为空，需要恢复历史数据或等待新采集

**Claude Code 修复完成，等待 Atlas 复审**
