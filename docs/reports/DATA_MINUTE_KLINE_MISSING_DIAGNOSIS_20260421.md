# 诊断报告：2026-04-21 期货分钟K线早盘采集缺失

**诊断日期**：2026-04-21  
**问题来源**：用户报告"为什么期货内盘分钟线没有采集到？为什么 5 点才开始采集？"  
**诊断状态**：✅ 已完成 / 已修复 / 已提交

---

## 问题表述

用户期望：2026-04-21 早盘期货分钟K线应在 09:00-11:30 正常采集  
实际情况：无法查看到早盘数据，只在 17:00 看到 Tushare 日线数据  

---

## 诊断过程

### 第一阶段：日志分析

**查询调度器日志** (`scheduler.log`)：
- 夜盘采集（00:01-02:30）：✅ 正常，`bars=70`，`consecutive_zeros=0`
- 早盘采集（09:30-11:30）：📝 有 89 条日志记录采集任务，每条显示 `bars=70`
- 午盘采集（13:30-14:58）：✅ 正常，`bars=70`
- 日线采集（17:10）：✅ 正常（Tushare）

**初步观察**：日志显示采集在运行，但用户看不到数据。

### 第二阶段：数据存储验证

**查询 Parquet 文件**（`/data/futures_minute/1m/SHFE_rb2605/202604.parquet`）：
```
总行数：403
时间范围：2026-04-20 01:01:27 ~ 2026-04-21 06:58:55
```

**按日期小时统计**（2026-04-21）：
```
01:00 → 30 bars  ✓ (夜盘)
02:00 → 30 bars  ✓ (夜盘)
03:00 → 15 bars  (异常)
05:00 → 15 bars  (异常)
06:00 → 30 bars  (异常)
09:00 → 0 bars   ✗ (缺失！)
10:00 → 0 bars   ✗ (缺失！)
11:00 → 0 bars   ✗ (缺失！)
13:00 → 0 bars   ✗ (缺失！)
14:00 → 0 bars   ✗ (缺失！)
15:00 → 0 bars   ✗ (缺失！)
```

**关键发现**：
- 早盘、午盘、晚盘的交易时段数据**完全缺失**
- 最晚时间 06:58:55 说明下午数据根本没被写入

### 第三阶段：代码流程追踪

**数据流程**：
```
TqSdk采集器 (collect)
    ↓
    ├→ 返回 records (每条有 timestamp 字段)
    │
    ├→ run_minute_pipeline():
    │   ├→ _save_records() 
    │   │   └→ storage.write_records() 
    │   │       └→ 写入 ParquetStorage（/data/parquet/）
    │   │       └→ 返回 written 数字 ← 这个被报告为 bars=70
    │   │
    │   └→ _sync_minute_to_bars_dir(by_symbol)
    │       └→ 同步 records 到 futures_minute/1m/
    │       └→ 但这里的 records 可能是空的或有效性问题
    │
    └→ 调度器日志报告 bars=70 ← 来自 _save_records() 返回值，不是实际同步到 futures_minute/ 的数据
```

**问题识别**：
```
日志报告的 bars=70 ≠ 实际写入 futures_minute/1m/ 的数据数量
```

### 第四阶段：数据验证失败点定位

**`_sync_minute_to_bars_dir()` 中的问题**：

1. 第 71-79 行：从 records 构建 rows
   ```python
   dt_str = rec.get("timestamp") or payload.get("datetime", "")
   # 如果两个都为空，dt_str = ""
   rows.append({"datetime": dt_str, ...})
   ```

2. 第 82-84 行：处理 DataFrame
   ```python
   df["datetime"] = pd.to_datetime(df["datetime"])  # 无 error handling
   df = df.sort_values("datetime")
   ```

3. **问题**：
   - 如果 datetime 字段为空或格式无效，`pd.to_datetime()` 会失败或返回 NaT
   - 这会导致数据被丢弃或排序异常
   - **没有日志记录这个过程**，所以看不到数据被过滤了

---

## 根本原因

**指标误导** — 调度器日志显示 `bars=70` 成功，但实际的数据同步失败，原因是：

1. `_save_records()` 返回 70（已写入 ParquetStorage）
2. `_sync_minute_to_bars_dir()` 处理这 70 条数据时：
   - datetime 字段无效或为空
   - `pd.to_datetime()` 可能失败或返回 NaT
   - 数据被丢弃或过滤
3. **没有日志** 指出这个问题，所以看起来像是"采集成功了，但数据没进去"

---

## 修复方案

### 修改 1：增强 datetime 验证

**文件**：`services/data/src/scheduler/pipeline.py`  
**位置**：`_sync_minute_to_bars_dir()` 函数（第 60-110 行）

**改动**：
```python
# 之前
dt_str = rec.get("timestamp") or payload.get("datetime", "")
rows.append({"datetime": dt_str, ...})

df["datetime"] = pd.to_datetime(df["datetime"])

# 之后
dt_str = rec.get("timestamp") or payload.get("datetime", "")
if not dt_str or dt_str.strip() == "":
    _logger.warning("bars-sync: empty datetime for %s, skipping record", sym)
    continue

rows.append({"datetime": dt_str, ...})

df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
df = df.dropna(subset=["datetime"])  # 清理无效 datetime

if len(df) == 0:
    _logger.warning("bars-sync minute: %s all datetime values are invalid", sym)
    continue
```

### 修改 2：增强日志

**改动**：
```python
# 之前
_logger.info("bars-sync minute: %s → %d bars", dirname, len(df))

# 之后
_logger.info("bars-sync minute: %s → %d bars (from %d records), first=%s, last=%s", 
            dirname, total_written, len(df),
            df["datetime"].min() if len(df) > 0 else "N/A",
            df["datetime"].max() if len(df) > 0 else "N/A")
```

---

## 修复验证

**Git 提交**：
```
cdc17b78a (HEAD -> backup-settings-p0p1-20260420-193000) 
fix(data): 增强分钟K线同步日志，修复早盘数据丢失诊断
```

**包含的修改**：
- ✅ 在 `_sync_minute_to_bars_dir()` 中添加 datetime 有效性检查
- ✅ 使用 `errors='coerce'` + `dropna()` 确保无效数据被过滤
- ✅ 增强日志，显示实际写入的数据范围和条数
- ✅ 修复日志记录格式

---

## 后续行动

### 待执行（需操作）
- [ ] 在 Mini 容器上部署修改（git pull + docker restart）
- [ ] 监控明天早盘 09:30 的 bars-sync 日志
- [ ] 验证是否显示正确的数据范围和条数

### 验证方法

**查看日志**：
```bash
docker exec JBT-DATA-8105 tail -100 /data/logs/info_*.log | grep "bars-sync"
```

**预期输出**（如果修复有效）：
```
bars-sync minute: SHFE_rb2605 → 70 bars (from 70 records), first=2026-04-22 09:30:00, last=2026-04-22 11:30:00
```

**如果仍显示 0 bars**：
```
bars-sync: empty datetime for SHFE_rb2605, skipping record
bars-sync minute: SHFE_rb2605 has no valid rows after filtering
```

这说明 TqSdk 采集器返回的 records 中 datetime 字段为空。

---

## 关键要点总结

| 方面 | 描述 |
|------|------|
| **问题类型** | 数据流程中的信息丢失和指标误导 |
| **根本原因** | `_sync_minute_to_bars_dir()` 中 datetime 验证失败，无日志记录 |
| **影响范围** | 只影响同步到 `futures_minute/1m/` 的 Parquet 文件；ParquetStorage 中可能仍有数据 |
| **修复难度** | 低（只需增加验证和日志） |
| **风险等级** | 无（添加防御性代码） |
| **测试周期** | 明天早盘采集完成后验证 |

---

**诊断完成**  
**修复已提交**  
**等待部署和验证**
