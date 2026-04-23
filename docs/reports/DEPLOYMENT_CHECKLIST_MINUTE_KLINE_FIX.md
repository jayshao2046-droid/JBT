# 部署清单：期货分钟K线采集缺失修复

**修复版本**：cdc17b78a、3a1a6eff5  
**修复范围**：services/data/src/scheduler/pipeline.py  
**部署目标**：Mini（192.168.31.74）  
**部署环境**：容器 JBT-DATA-8105  
**部署截止**：明天早盘之前（2026-04-22 09:00）

---

## 部署步骤

### 步骤 1：在 Mini 上拉取最新代码

```bash
ssh jaybot@192.168.31.74
cd ~/JBT
git fetch origin
git checkout backup-settings-p0p1-20260420-193000
git pull origin backup-settings-p0p1-20260420-193000
```

**预期结果**：
```
Already up to date.
# 或
Updating xxx...yyy (2 files changed)
```

### 步骤 2：验证代码修改

```bash
grep -n "errors=\"coerce\"" services/data/src/scheduler/pipeline.py
```

**预期结果**：
```
97:            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
```

### 步骤 3：重启容器应用修改

```bash
docker restart JBT-DATA-8105
```

**预期结果**：容器重启，日志显示调度器重新初始化

### 步骤 4：验证容器状态

```bash
docker ps | grep DATA-8105
docker logs JBT-DATA-8105 | tail -20
```

**预期结果**：容器在运行，最后 20 行日志显示"已注册 39 个任务"

---

## 验证方案

### 验证 A：监控早盘采集日志

**执行时间**：2026-04-22 09:30+  
**命令**：
```bash
docker exec JBT-DATA-8105 tail -100 /data/logs/info_*.log | grep "bars-sync"
```

**成功标志**：
```
bars-sync minute: SHFE_rb2605 → 70 bars (from 70 records), first=2026-04-22 09:30:00, last=2026-04-22 09:32:00
```

**失败标志**（需要进一步调查）：
```
bars-sync: empty datetime for SHFE_rb2605, skipping record
bars-sync minute: SHFE_rb2605 has no valid rows after filtering
```

### 验证 B：检查数据文件

**执行时间**：2026-04-22 12:00+  
**命令**：
```bash
ssh jaybot@192.168.31.74
python3 << 'EOF'
import pyarrow.parquet as pq
import pandas as pd

t = pq.read_table('~/jbt-data/futures_minute/1m/SHFE_rb2605/202604.parquet')
df = t.to_pandas()
df['datetime'] = pd.to_datetime(df['datetime'])

# 按日期统计
df_today = df[df['datetime'].dt.date == pd.Timestamp('2026-04-22').date()]
print(f"2026-04-22 数据行数: {len(df_today)}")
if len(df_today) > 0:
    print(f"时间范围: {df_today['datetime'].min()} ~ {df_today['datetime'].max()}")
    hourly = df_today.groupby(df_today['datetime'].dt.hour).size()
    for hour, count in hourly.items():
        print(f"  {hour:02d}:00 → {count} bars")
EOF
```

**成功标志**：
```
2026-04-22 数据行数: 70+
时间范围: 2026-04-22 09:30:00 ~ 2026-04-22 14:58:00
  09:00 → 30 bars
  10:00 → 30 bars
  11:00 → 10 bars
  13:00 → ... (下午数据)
```

**失败标志**：
```
2026-04-22 数据行数: 0
# 或
时间范围只到早上 06:58
```

---

## 故障排查

| 症状 | 可能原因 | 排查方法 |
|------|--------|--------|
| bars-sync 显示 0 bars | datetime 无效或为空 | 检查 TqSdk 采集器返回的 records 格式 |
| 日志中没有 bars-sync 信息 | 日志级别配置或 datetime 完全为空 | 检查 `/data/logs/error_*.log` |
| 容器启动失败 | 代码语法错误或导入失败 | `docker logs JBT-DATA-8105` 查看错误 |
| 修改未应用 | Git pull 失败 | `git status` 和 `git log` 检查分支状态 |

---

## 回滚方案

如果修复导致问题，执行回滚：

```bash
cd ~/JBT
git revert cdc17b78a  # 或 git reset --hard HEAD~2
docker restart JBT-DATA-8105
```

---

## 备注

- 修复已通过本地代码验证（errors="coerce" 已确认在源码中）
- Git 提交已完成，可随时部署
- 修复是防御性的（只添加验证和日志，不改变核心逻辑）
- 部署风险低，验证周期短（明天早盘即可看到效果）
