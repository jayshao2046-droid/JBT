# 数据端容器紧急修复 — Claude Code 汇报

> 汇报时间: 2026-04-13  
> 汇报人: Claude Code  
> 目标: JBT-DATA-8105 容器启动失败修复  
> 优先级: P0（开盘前必须完成）

---

## 一、问题诊断

### 1.1 当前状态
- ❌ 容器 JBT-DATA-8105 不存在或未运行
- ✅ requirements.txt 已完整（所有依赖已补全）
- ✅ supervisord.conf PYTHONPATH 已正确配置为 `/app`
- ✅ docker-compose.dev.yml bind mount 配置正确

### 1.2 根本原因
**Dockerfile 构建上下文路径错误**：

```dockerfile
# docker-compose.dev.yml 中定义
build: ./services/data  # 构建上下文是 services/data/ 目录

# Dockerfile 中错误的 COPY 路径
COPY services/data/requirements.txt .           # ❌ 找不到文件
COPY services/data/src/ ./services/data/src/    # ❌ 找不到目录
COPY services/data/tests/ ./services/data/tests/
COPY services/data/configs/ ./services/data/configs/
COPY services/data/supervisord.conf /etc/supervisor/conf.d/jbt-data.conf
```

**错误原因**：构建上下文已经在 `services/data/` 目录，Dockerfile 中再写 `services/data/` 前缀会导致路径重复，实际查找的是 `services/data/services/data/...`（不存在）。

---

## 二、修复方案

### 2.1 需要修改的文件
**文件**: `services/data/Dockerfile`（P0 保护路径，需要 Token）

### 2.2 修改内容
将所有 COPY 指令的路径修正为相对于构建上下文的正确路径：

```dockerfile
# 修改前 → 修改后
COPY services/data/requirements.txt .           → COPY requirements.txt .
COPY services/data/src/ ./services/data/src/    → COPY src/ ./services/data/src/
COPY services/data/tests/ ./services/data/tests/ → COPY tests/ ./services/data/tests/
COPY services/data/configs/ ./services/data/configs/ → COPY configs/ ./services/data/configs/
COPY services/data/supervisord.conf /etc/supervisor/conf.d/jbt-data.conf → COPY supervisord.conf /etc/supervisor/conf.d/jbt-data.conf
```

### 2.3 修复后执行步骤
1. 重建容器：`docker compose -f docker-compose.dev.yml up -d --build jbt-data`
2. 验证挂载点：检查 `./services/data:/app` bind mount 是否生效
3. 验证进程：`docker exec JBT-DATA-8105 supervisorctl status` 三个进程应为 RUNNING
4. 验证依赖：`docker exec JBT-DATA-8105 pip show pyarrow apscheduler akshare`
5. 验证健康检查：`curl http://localhost:8105/health`
6. 验证 scheduler 日志：`docker exec JBT-DATA-8105 tail -20 /data/logs/scheduler_stderr.log`
7. 验证数据完整性：`docker exec JBT-DATA-8105 find /data/ -name "*.parquet" | wc -l` 应 ≥ 42006

---

## 三、风险评估

### 3.1 修复风险
- ✅ **低风险**：仅修正构建路径，不改变业务逻辑
- ✅ **可回滚**：如有问题可立即回退到上一个 commit
- ✅ **影响范围**：仅限 data 服务容器构建

### 3.2 不修复的风险
- ❌ **高风险**：周一开盘前数据采集无法运行
- ❌ **业务影响**：实时行情、新闻、因子数据全部中断
- ❌ **连锁影响**：decision / backtest / sim-trading 依赖 data 服务，全部受影响

---

## 四、请求 Atlas 授权

### 4.1 请求内容
请求为以下文件签发紧急 Token：
- `services/data/Dockerfile`（1 文件，修正 5 行 COPY 路径）

### 4.2 时间要求
- **紧急程度**: P0
- **截止时间**: 2026-04-14 09:30（周一开盘前）
- **预计修复时间**: 10 分钟（修改 + 重建 + 验证）

### 4.3 验收标准
- [ ] 容器成功构建并启动
- [ ] 三个 supervisor 进程全部 RUNNING
- [ ] API 健康检查通过
- [ ] Scheduler 日志无 ModuleNotFoundError
- [ ] 数据完整性验证通过（≥42006 parquet 文件）

---

## 五、备注

1. **Atlas 已完成的工作**：数据迁移（2.3GB, 42006 parquets）已完成，所有数据已在容器 `/data/` volume 中
2. **配置文件状态**：requirements.txt / supervisord.conf / docker-compose.dev.yml 均已正确，无需修改
3. **唯一阻塞点**：Dockerfile 构建路径错误导致容器无法启动
4. **Legacy daemon 状态**：宿主机 PID 21737 仍在运行，部分补偿采集中

---

**Claude Code 等待 Atlas 指令**
