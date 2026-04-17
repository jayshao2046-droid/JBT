# 期货分钟K线数据回补工具

## 📁 目录结构

```
data_backfill/
├── README.md              # 本文档
├── scripts/               # 工具脚本
│   ├── backfill_futures_minute.py   # 回补脚本
│   └── verify_and_import.py         # 验证和导入脚本
├── output/                # 回补数据输出目录（临时）
└── logs/                  # 日志目录
    ├── backfill.log       # 回补日志
    └── verify.log         # 验证日志
```

## 🎯 功能说明

本工具用于回补期货分钟K线数据的缺失时间段，支持以下35个连续合约品种：

### 郑商所 (CZCE) - 10个品种
- CF (棉花), FG (玻璃), MA (甲醇), OI (菜油), PF (短纤)
- RM (菜粕), SA (纯碱), SR (白糖), TA (PTA), UR (尿素)

### 大商所 (DCE) - 15个品种
- a (豆一), c (玉米), eb (苯乙烯), i (铁矿石), j (焦炭)
- jd (鸡蛋), jm (焦煤), l (塑料), lh (生猪), m (豆粕)
- p (棕榈油), pg (液化气), pp (PP), v (PVC), y (豆油)

### 上期所 (SHFE) - 10个品种
- ag (白银), al (铝), au (黄金), cu (铜), hc (热卷)
- rb (螺纹钢), ru (橡胶), sp (纸浆), ss (不锈钢), zn (锌)

## 🔧 工作原理

利用 **TqSdk 的回测机制** 来补全分钟K线：
1. 通过模拟回测过程，强制 TqSdk 从服务器拉取缺失的历史数据
2. 将数据保存到临时目录 `output/`
3. 验证数据完整性和正确性
4. 合并到正式目录 `/Users/jaybot/JBT/data/futures_minute/1m/`
5. 清除临时数据

## 📝 使用步骤

### 1️⃣ 回补数据

```bash
cd /Users/jaybot/JBT/data_backfill/scripts

python3 backfill_futures_minute.py \
  --start 2026-04-10 \
  --end 2026-04-17 \
  --account YOUR_TQSDK_ACCOUNT \
  --password YOUR_TQSDK_PASSWORD
```

**参数说明：**
- `--start`: 开始日期（格式：YYYY-MM-DD）
- `--end`: 结束日期（格式：YYYY-MM-DD）
- `--account`: 天勤账号
- `--password`: 天勤密码
- `--symbols`: （可选）指定回补的合约列表，不指定则回补全部35个
- `--output`: （可选）输出目录，默认为 `/Users/jaybot/JBT/data_backfill/output`

**示例：仅回补部分品种**
```bash
python3 backfill_futures_minute.py \
  --start 2026-04-10 \
  --end 2026-04-17 \
  --account YOUR_ACCOUNT \
  --password YOUR_PASSWORD \
  --symbols "KQ.m@SHFE.rb" "KQ.m@SHFE.hc" "KQ.m@DCE.i"
```

### 2️⃣ 验证数据

```bash
python3 verify_and_import.py \
  --verify \
  --start 2026-04-10 \
  --end 2026-04-17
```

**验证内容：**
- 检查数据文件是否存在
- 检查数据时间范围是否覆盖目标时间段
- 检查数据记录数是否合理
- 检查数据格式是否正确

### 3️⃣ 导入数据（模拟运行）

```bash
python3 verify_and_import.py \
  --import \
  --dry-run
```

**说明：**
- `--dry-run` 模式仅模拟运行，不实际写入数据
- 用于预览导入操作，确认无误后再执行实际导入

### 4️⃣ 正式导入数据

```bash
python3 verify_and_import.py \
  --import
```

**导入逻辑：**
- 如果目标文件已存在，合并数据并去重（保留最新记录）
- 如果目标文件不存在，直接创建新文件
- 按月份分组保存（例如：202604.parquet）

### 5️⃣ 清除临时数据

```bash
python3 verify_and_import.py \
  --import \
  --clean
```

**说明：**
- `--clean` 参数会在导入成功后自动清除 `output/` 目录下的所有回补数据
- 保留目录结构和工具脚本

## 🔍 日志查看

```bash
# 查看回补日志
tail -f /Users/jaybot/JBT/data_backfill/logs/backfill.log

# 查看验证日志
tail -f /Users/jaybot/JBT/data_backfill/logs/verify.log
```

## ⚠️ 注意事项

1. **天勤账号限制**：
   - 确保天勤账号有足够的权限访问历史数据
   - 回补大量数据时可能受到 API 频率限制

2. **数据完整性**：
   - 期货市场有夜盘和日盘，确保回补时间段覆盖完整交易时段
   - 节假日和非交易日不会有数据

3. **磁盘空间**：
   - 回补数据会占用临时空间，确保 `output/` 目录有足够空间
   - 导入后及时清除临时数据

4. **数据合并**：
   - 导入时会自动合并已有数据，去重逻辑为保留最新记录
   - 建议先用 `--dry-run` 模式预览

## 🚀 快速回补（一键执行）

**推荐方式：使用一键脚本**

```bash
cd /Users/jaybot/JBT/data_backfill
./run_backfill.sh
```

脚本会自动完成：
1. 回补所有35个品种的数据
2. 验证数据完整性
3. 导入到正式目录
4. 清除临时数据

**手动执行方式：**

```bash
cd /Users/jaybot/JBT/data_backfill/scripts

# 1. 回补数据
python3 backfill_futures_minute.py \
  --start 2026-04-10 \
  --end 2026-04-17 \
  --account YOUR_ACCOUNT \
  --password YOUR_PASSWORD

# 2. 验证数据
python3 verify_and_import.py \
  --verify \
  --start 2026-04-10 \
  --end 2026-04-17

# 3. 导入并清除
python3 verify_and_import.py \
  --import \
  --clean
```

## 📊 数据格式

回补数据采用 Parquet 格式，字段包括：
- `datetime`: 时间戳（pandas datetime64）
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `open_oi`: 开盘持仓量
- `close_oi`: 收盘持仓量

## 🔄 后续使用

如需再次回补数据，直接按照上述步骤执行即可。工具会自动：
- 检测已有数据
- 合并新旧数据
- 去重并排序
- 保持数据连续性

## 📞 问题排查

1. **回补失败**：
   - 检查天勤账号是否正常
   - 检查网络连接
   - 查看日志文件定位具体错误

2. **验证失败**：
   - 检查回补的时间段是否正确
   - 检查是否有交易日数据
   - 查看日志了解具体原因

3. **导入失败**：
   - 检查目标目录权限
   - 检查磁盘空间
   - 确认数据格式正确

---

**最后更新**: 2026-04-17  
**维护者**: JBT Team
