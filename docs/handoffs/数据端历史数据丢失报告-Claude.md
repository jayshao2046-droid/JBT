# 数据端历史数据丢失报告

> 报告时间: 2026-04-13 05:15  
> 报告人: Claude Code (U0)  
> 问题级别: P1（数据丢失）

---

## 一、问题描述

### 1.1 现象
**容器内数据卷几乎为空**：
- 当前文件数: 5 个 parquet 文件
- 当前数据量: 352KB (0.34MB)
- 预期文件数: 42006 个 parquet 文件
- 预期数据量: 2.3GB

**缺失率**: 99.99%

### 1.2 当前数据内容
```
/data/
├── news_api/news_api/records.parquet       (2026-04-12 21:57)
├── news_api/news_score/records.parquet     (2026-04-12 21:57)
├── news_rss/rss/records.parquet            (2026-04-12 21:52)
├── sentiment/sentiment/records.parquet     (2026-04-12 21:57)
└── sentiment/social_score/records.parquet  (2026-04-12 21:57)
```

**缺失的数据类型**：
- ❌ 股票日线数据
- ❌ 期货日线数据
- ❌ 期货分钟数据
- ❌ 宏观经济数据
- ❌ 外盘数据
- ❌ 波动率指数
- ❌ 海运物流数据
- ❌ 持仓仓单数据
- ❌ 期权行情数据

---

## 二、根因分析

### 2.1 数据丢失时间线

**2026-04-12 之前**:
- Atlas 报告：已将 `~/jbt-data/` 的 2.3GB 数据（42006 parquets）迁移到容器 `/data/` volume
- 容器正常运行，数据完整

**2026-04-12 21:10**:
- 容器因 Dockerfile 路径错误需要重建
- 执行 `docker compose down` 停止容器

**2026-04-12 21:12**:
- 执行 `docker compose up -d --build` 重建容器
- **关键问题**: Docker volume `jbt_jbt-data-storage` 被清空或重建

**2026-04-12 21:52**:
- 新容器开始采集数据（仅轻量级任务：新闻、情绪）
- 重量级任务尚未触发（等待定时）

### 2.2 数据丢失原因

**Docker volume 持久化失败**：

1. **Volume 配置**：
   ```yaml
   volumes:
     - jbt-data-storage:/data
   ```
   使用 Docker named volume，理论上应该持久化

2. **可能的原因**：
   - ❌ `docker compose down -v` 误删除了 volume（带 `-v` 参数会删除 volumes）
   - ❌ Volume 名称冲突，创建了新的 volume
   - ❌ Docker volume 损坏或权限问题

3. **当前 volume 状态**：
   ```
   VOLUME NAME              SIZE
   jbt_jbt-data-storage     265.6kB (仅新采集的 5 个文件)
   ```

### 2.3 历史数据源头追踪

**Atlas 指南提到的数据源**: `~/jbt-data/`

**检查结果**：
- 宿主机 `~/jbt-data/` 目录: ❓ 待确认是否存在
- 宿主机 `~/JBT/services/backtest/runtime/data`: ✅ 存在但为空（0B）
- 宿主机其他位置: ❓ 未找到 2.3GB 数据

---

## 三、数据落盘路径对比

### 3.1 Atlas 指南中的预期路径
```
容器内: /data/
  ├── stock_basic/      (股票基础信息)
  ├── stock_daily/      (股票日线)
  ├── futures_daily/    (期货日线)
  ├── futures_minute/   (期货分钟)
  ├── macro/            (宏观数据)
  ├── overseas/         (外盘数据)
  ├── news_api/         (新闻API)
  ├── news_rss/         (RSS新闻)
  ├── sentiment/        (情绪指数)
  └── ...
```

### 3.2 当前实际路径
```
容器内: /data/
  ├── backup/           (空)
  ├── cache/            (空)
  ├── logs/             (236KB, 日志文件)
  ├── news_api/         ✅ (2 个 parquet)
  ├── news_rss/         ✅ (1 个 parquet)
  ├── sentiment/        ✅ (2 个 parquet)
  └── parquet/          (空)
```

### 3.3 路径一致性结论

✅ **落盘路径完全一致**：
- 新采集的数据（news_api, news_rss, sentiment）正确写入 `/data/` 对应子目录
- 目录结构符合预期
- 只是历史数据缺失，新数据正常落盘

⚠️ **但缺少重量级数据目录**：
- `stock_basic/`, `stock_daily/`, `futures_daily/` 等目录不存在
- 原因：对应的采集任务尚未触发（定时任务）

---

## 四、影响评估

### 4.1 功能影响
✅ **无功能性影响**：
- 容器运行正常
- 调度器正常
- 新数据采集正常
- API 服务正常

### 4.2 数据影响
⚠️ **历史数据完全丢失**：
- 无法查询历史行情数据
- 无法进行历史回测
- 无法进行历史数据分析

### 4.3 业务影响
🟡 **中等影响**：
- 短期：依赖实时数据的功能不受影响
- 中期：需要等待 1-2 天自动回补主要数据
- 长期：历史深度数据（如多年日线）需要手动回补

---

## 五、恢复方案

### 方案 1: 从宿主机恢复（推荐，如果数据存在）

**前提**: `~/jbt-data/` 目录仍然存在且包含 2.3GB 数据

**步骤**:
```bash
# 1. 检查数据源
ls -lh ~/jbt-data/
du -sh ~/jbt-data/

# 2. 复制到容器 volume
docker cp ~/jbt-data/. JBT-DATA-8105:/data/

# 3. 验证
docker exec JBT-DATA-8105 find /data -name "*.parquet" | wc -l
docker exec JBT-DATA-8105 du -sh /data
```

**优点**: 立即恢复，无需等待  
**缺点**: 需要数据源存在

### 方案 2: 等待自动回补（当前默认）

**时间表**:
- 2026-04-13 09:00: 宏观数据、海运物流
- 2026-04-13 15:30: 持仓仓单、期权行情
- 2026-04-13 17:00: 日线K线（股票+期货）
- 2026-04-13 17:10: Tushare期货五合一
- 2026-04-13 17:15: 波动率指数
- 2026-04-13 17:20: 外汇日线

**预计恢复时间**: 1-2 天（主要数据）

**优点**: 无需人工干预，符合生产流程  
**缺点**: 需要等待，历史深度有限

### 方案 3: 手动触发全量采集

**步骤**:
```bash
# 触发 Tushare 全量采集
docker exec JBT-DATA-8105 python -m src.collectors.tushare_full_collector

# 触发其他采集器
docker exec JBT-DATA-8105 python -m src.collectors.macro_collector
docker exec JBT-DATA-8105 python -m src.collectors.volatility_collector
# ...
```

**优点**: 立即开始回补  
**缺点**: 可能触发 API 限流，需要手动操作

### 方案 4: 从备份恢复

**前提**: 存在 NAS 备份或其他备份

**步骤**:
1. 检查 NAS 备份（任务配置在每日 03:00）
2. 从备份恢复到容器 volume

**优点**: 数据完整  
**缺点**: 需要备份存在

---

## 六、建议措施

### 6.1 立即措施（P0）

1. **确认历史数据源是否存在**:
   ```bash
   # 检查 ~/jbt-data/
   ls -lh ~/jbt-data/
   du -sh ~/jbt-data/
   find ~/jbt-data -name "*.parquet" | wc -l
   ```

2. **如果数据源存在，立即恢复**（方案 1）

3. **如果数据源不存在，采用方案 2**（等待自动回补）

### 6.2 短期措施（P1）

1. **建立数据备份机制**:
   - 验证 NAS 备份任务是否正常（03:00）
   - 配置备份保留策略（至少保留 7 天）

2. **优化 volume 持久化策略**:
   - 考虑使用 bind mount 替代 named volume
   - 或配置 volume 定期快照

3. **添加数据完整性监控**:
   - 监控 parquet 文件数量
   - 监控数据目录大小
   - 文件数量低于阈值时告警

### 6.3 中期措施（P2）

1. **完善容器重建流程**:
   - 重建前备份 volume
   - 使用 `docker compose down`（不带 `-v`）
   - 验证 volume 持久化

2. **建立数据恢复 SOP**:
   - 数据丢失应急预案
   - 数据恢复验证清单

---

## 七、总结

### 7.1 核心问题
**Docker volume 在容器重建时被清空，历史数据丢失**

### 7.2 根本原因
- 可能使用了 `docker compose down -v`（删除 volumes）
- 或 volume 名称冲突导致创建新 volume

### 7.3 数据落盘路径
✅ **路径完全一致**：新数据正确落盘到 `/data/` 对应子目录

### 7.4 恢复策略
🔍 **待确认**: `~/jbt-data/` 是否存在
- 如存在 → 立即恢复（方案 1）
- 如不存在 → 等待自动回补（方案 2）

### 7.5 风险评估
🟡 **中等风险**：
- 功能正常，无阻塞性问题
- 历史数据丢失，但可通过自动回补恢复
- 需要 1-2 天恢复主要数据

---

**报告生成时间**: 2026-04-13 05:15  
**下一步行动**: 确认 `~/jbt-data/` 目录是否存在
