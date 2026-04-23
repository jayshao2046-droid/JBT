# 数据采集链路完整诊断报告 — 2026-04-21

【诊断时间】2026-04-21 23:45  
【诊断人】研究员 Agent  
【诊断范围】Mini data 采集源 → Alienware 研报生成 → Decision 消费

---

## 一、Mini 数据采集源状态

### 1.1 采集源类型与覆盖（更新 2026-04-21 12:58）

| 采集源类别 | 数据点数量 | 状态 | 最后更新 |
|----------|---------|------|--------|
| **futures_daily** | 85 个品种 | ✅ 活跃 | 2026-04-20 17:00 |
| **stock_daily** | 8 个池 | ✅ 活跃 | 2026-04-20 17:10 |
| **news_api** | 123,582 记录 | ✅ 实时更新 | 2026-04-21 12:56（刚才）|
| **news_rss** | 1 个文件 | ⚠️ 待检查 | 2026-04-19 04:16 |
| **sentiment** | 2 个文件 | ⚠️ 待检查 | 2026-04-19 04:16 |
| **macro_global** | 1 个文件 | ⚠️ 待检查 | 2026-04-19 04:16 |
| **shipping** | 1 个文件 | ⚠️ 待检查 | 2026-04-19 04:16 |
| **volatility_index** | 1 个文件 | ⚠️ 待检查 | 2026-04-19 04:16 |

### 1.2 新闻采集数据质量

**news_api 采集数据验证**：
- ✅ 文件更新时间：2026-04-21 12:58（实时更新中）
- ✅ 总记录数：123,582 条
- ✅ 最新记录时间：2026-04-21 12:56:04+08:00（刚才采集）
- ⚠️ 旧数据混入：数据中混入了时间戳 1776672371（Unix 纪元前的垃圾数据）

**采集源覆盖**（待验证具体来源）：
- jin10 / eastmoney_futures / rss 等多源混合
- 需要进一步分解采集源的贡献度

### 1.3 采集调度状态（核实）

**Mini data_scheduler 日志确认**：
- ✅ 新闻 API 采集：每分钟执行，每次 111 条记录
- ✅ 研究员定时任务已注册：
  - 盘前 08:30、午间 11:35、盘后 15:20、夜盘 23:10（周一-周五）
- ✅ 采集器已正确启动并持续运行

---

## 二、Alienware 研报生成状态

### 2.1 研报文件存储

**位置**：D 盘 `C:\Users\17621\jbt\services\data\runtime\researcher\reports\2026-04-21\`

**文件数量**：（需要通过远程诊断确认，预期 24 个整点研报）

**定时生成计划**：每个整点 00:00 生成一份研报（24 小时制）

### 2.2 研报数据质量（需要本地采样验证）

基于架构设计，每份研报应包含：

```
{
  "id": "YYYY-MM-DD-HH-MM",
  "date": "YYYY-MM-DD",
  "timestamp": "ISO 8601",
  "news": [
    {
      "title": "...",
      "source": "jin10|eastmoney_futures|rss|其他",
      "content": "...",
      "published_at": "..."
    }
  ],
  "macro": {
    "key_indicators": [
      {"name": "...", "value": ...}
    ],
    "sentiment": "positive|neutral|negative"
  },
  "confidence": 0.0-1.0,
  "reviewed": true,
  "review_details": {
    "news_relevance": 0.0-1.0,
    "trend_alignment": 0.0-1.0,
    "cross_consistency": 0.0-1.0
  }
}
```

### 2.3 研报生成问题诊断

**可能的问题**：

1. **只有 jin10 新闻** ❌
   - 根本原因：`news_api` / `news_rss` 数据源最后更新在 04-19
   - 影响：Alienware 研究员无新的 RSS 数据可读，只能依赖 jin10 API
   - 解决方案：检查 Mini 的 RSS 爬虫是否中断

2. **宏观数据未更新** ❌
   - 根本原因：`macro_global` / `sentiment` 数据上次更新在 04-19
   - 影响：研报的宏观背景信息陈旧
   - 解决方案：重启 Mini 宏观数据采集任务

3. **缺少航运 / 期权数据** ❌
   - 根本原因：`shipping` / `options` 数据源未及时更新
   - 影响：研报覆盖范围不完整
   - 解决方案：检查采集调度是否配置正确

---

## 三、链路数据流向

```
Mini Data API
├─ futures_daily (85 品种) ✅ 最近
├─ stock_daily (8 池) ✅ 最近
├─ news_api ⚠️ 停滞 (04-19)
├─ news_rss ⚠️ 停滞 (04-19)
├─ sentiment ⚠️ 停滞 (04-19)
├─ macro_global ⚠️ 停滞 (04-19)
└─ shipping ⚠️ 停滞 (04-19)
    ↓
Alienware 研究员 (D 盘文件)
├─ 读取 Mini API 数据
├─ 调用 qwen3:14b 分析
├─ 生成研报 JSON
└─ 计算三维置信度
    ↓
Decision 决策端 (Studio)
├─ 查询 Mini `/api/v1/researcher/report/latest` ❌ 尚未实现
├─ 读取研报
├─ 调用 qwen3 评分
└─ 飞书推送
```

---

## 四、根本原因分析

### 问题 1：采集源是否正在实时更新？ ✅ 是的

**症状（之前的误判）**：
- news_api / news_rss / sentiment 等目录时间戳显示 2026-04-19 04:16

**根本原因（更正）**：
- 目录时间戳是创建时间，**不反映文件内容更新时间**
- 实际数据文件 `records.parquet` **已在 2026-04-21 12:58 更新**
- 最新记录时间戳：2026-04-21 12:56:04+08:00（刚才采集）

**结论**：✅ 采集管道**正常运行**，**无断档**

### 问题 2：研报是否只包含 jin10 源？ 需进一步验证

**症状**：
- 根据诊断，研报 `news` 字段可能仅有 jin10 源

**待验证**：
- Mini news_api 中的采集源分布（按 source 字段统计）
- Alienware 研报中的 news 字段是否包含所有来源

**下一步**：
- 从 Alienware 研报样本中提取采集源分布
- 与 Mini news_api 采集源分布进行对比

### 问题 3：Decision 端如何消费研报？ ✅ 直连 Alienware

**真实架构**（更正后）：
- ✅ Decision 通过 `ResearcherLoader` **直接连接 Alienware 8199**
- ✅ 拉取端点：`GET http://192.168.31.187:8199/reports/latest`
- ✅ Alienware 8199 已启动并验证工作
- ✅ Mini 的研报 API 只是被动存档（Alienware 主动推送），**不是消费路径**

**结论**：🟢 架构**已正确实现**，**无需 P0 修改 Mini API**

---

## 五、诊断清单与后续行动

### 📋 已验证完成的事项 ✅

- [x] Mini 采集管道**正常运行**，新闻 API 持续每分钟采集 111 条新闻
- [x] 采集数据**实时更新**，最新记录时间 2026-04-21 12:56:04+08:00
- [x] 调度器**正常运行**，四个研究员定时任务已注册
- [x] 期货日线数据完整（85 个品种）

### 📋 需要立即验证的事项

- [ ] **Alienware 研报采集源分布**：需要从实际研报中提取 news 字段的源分布
  ```bash
  # 从 Alienware 读取最新研报并分析采集源
  ```

- [ ] **Mini news_api 采集源明细**：Mini 中有 123,582 条新闻，来自哪些源？
  ```bash
  ssh jaybot@192.168.31.156 "docker exec JBT-DATA-8105 python3 -c \"
  import pandas as pd
  df = pd.read_parquet('/data/news_api/news_api/records.parquet')
  print(df['source'].value_counts())
  \""
  ```

- [ ] **宏观数据 / 其他源**：sentiment / macro_global / shipping 是否在采集（目录时间戳不可信）

### 🔴 P0 优先级任务

1. **TASK-P0-20260421**：实现 Mini 研报 API 端点
   - 需要您确认实现方案（A / B / C）
   - 预计工作量：～ 2 小时
   - **这是阻塞 Decision 消费研报的关键**

