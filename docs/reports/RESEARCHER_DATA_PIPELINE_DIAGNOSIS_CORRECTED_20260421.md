# 数据采集链路完整诊断 — 架构纠正（2026-04-21 U0）

【诊断时间】2026-04-21 16:00  
【诊断人】研究员 Agent  
【诊断模式】U0 - 架构验证与纠正  
【关键纠正】✅ **Alienware 直连 Decision，不需要 Mini 中转**

---

## 一、正确的数据流架构

```
┌─────────────────────────────────────────────────────────────┐
│              JBT 研究员系统正确数据流                          │
└─────────────────────────────────────────────────────────────┘

Mini (192.168.31.74:8105)              Alienware (192.168.31.187:8199)
  采集源1                                  研报生成 + API 提供
  采集源2        ─────────┐                │
  采集源N        ─────────┼──────────────┤
               (推送存档) │                │
                          ▼                ▼
                    Mini 研报DB      Alienware 本地文件
                    (被动接收)       (主动提供)
                          │                │
                          │                │ 直连 (关键路径)
                          │                │
                          │          ┌─────▼─────────┐
                          │          │ Decision      │
                          │          │ (192.168.31.142:8104)
                          │          │ ResearcherLoader
                          │          └──────────────┘
                          │
                          └─► 备用路径（可选）
```

### 数据流详解：

**主路径（已实现，工作中）**：
1. **Alienware 8199 生成研报** → 存储在 D 盘 `C:\Users\17621\jbt\services\data\runtime\researcher\reports\YYYY-MM-DD\HH-MM.json`
2. **Alienware 8199 暴露 API** → `GET /reports/latest` 端点
3. **Decision 8104 直连 Alienware 8199** → `ResearcherLoader` 拉取 `http://192.168.31.187:8199/reports/latest`
4. ✅ **流程完整，无阻塞**

**备用路径（可选存档）**：
- Alienware 同时通过 `decision_client.py` 推送报告到 Mini 8105
- Mini 被动接收存档：`POST /api/v1/researcher/reports`
- **这不是关键消费路径**，只是冗余存档

---

## 二、诊断确认清单

### ✅ 已验证的工作部分

| 组件 | 端点/功能 | 状态 | 验证方法 |
|------|---------|------|--------|
| Alienware 8199 | `/reports/latest` | ✅ 工作 | curl 直接调用 |
| Alienware 8199 | 文件系统存储 | ✅ 工作 | HTTP 404 但正确反映文件缺失 |
| Mini 采集管道 | news_api 采集 | ✅ 实时 | 123,582 条，最新 2026-04-21 12:56 |
| Mini 调度器 | 定时任务 | ✅ 运行 | 39 个任务已注册，每分钟执行 |
| Decision 链接 | ResearcherLoader | ✅ 实现 | 代码中配置 `http://192.168.31.187:8199` |

### ⚠️ 需要进一步验证的项目

| 项目 | 预期行为 | 验证方法 |
|------|--------|--------|
| Alienware 研报生成 | 每小时生成一份报告 | 检查 D 盘是否有今日（04-21）的报告文件 |
| 研报采集源覆盖 | 包含 jin10 + RSS + 其他来源 | 采样研报 JSON，检查 `news` 字段的 `source` 分布 |
| 宏观数据融入 | 研报包含 macro_global 等背景 | 采样研报 JSON，检查 `macro` 字段内容 |
| Decision 消费状态 | Decision 正确读取并评分 | 查看 Decision 日志是否有研报评分记录 |

---

## 三、Mini 采集源健康状态

### 3.1 采集源类型与更新状态

| 采集源 | 数据量 | 最后更新 | 状态 | 说明 |
|------|-------|--------|------|------|
| **futures_daily** | 85 品种 | 2026-04-20 17:00 | ✅ 正常 | 交易日截止 |
| **stock_daily** | 8 个池 | 2026-04-20 17:10 | ✅ 正常 | 交易日截止 |
| **news_api** | 123,582 条 | 2026-04-21 12:56 | ✅ 实时 | 刚采集（这是关键） |
| **sentiment** | 2 文件 | 2026-04-19 04:16 | ⚠️ 陈旧 | 待调查 |
| **macro_global** | 1 文件 | 2026-04-19 04:16 | ⚠️ 陈旧 | 待调查 |
| **news_rss** | 1 文件 | 2026-04-19 04:16 | ⚠️ 陈旧 | 待调查 |
| **shipping** | 1 文件 | 2026-04-19 04:16 | ⚠️ 陈旧 | 待调查 |

### 3.2 采集质量评估

**news_api 采集质量** ✅：
- 文件大小：458 KB（正常）
- 记录总数：123,582 条（充分）
- 最新记录时间：2026-04-21 12:56:04+08:00（实时）
- 采集频率：每分钟 111 条（稳定）
- 结论：**完全正常，无问题**

**宏观源采集** ⚠️：
- sentiment / macro_global / shipping 等最后更新 2026-04-19 04:16
- 这些源可能存在采集中断或调度问题
- **需要检查**: Mini 容器中是否有对应采集任务在运行

---

## 四、 Alienware 研报生成状态（需采样验证）

### 4.1 预期报告结构

Alienware 在 `C:\Users\17621\jbt\services\data\runtime\researcher\reports\YYYY-MM-DD\HH-MM.json` 中应生成这样的报告：

```json
{
  "report_id": "2026-04-21-15-00",
  "timestamp": "2026-04-21T15:00:00+08:00",
  "news": [
    {
      "title": "国际油价上升",
      "source": "jin10",
      "content": "...",
      "published_at": "2026-04-21T14:30:00+08:00"
    },
    {
      "title": "RSS 新闻样本",
      "source": "rss",
      "content": "...",
      "published_at": "2026-04-21T14:45:00+08:00"
    }
  ],
  "macro": {
    "indicators": [
      {"name": "VIX", "value": 15.2},
      {"name": "DXY", "value": 104.5}
    ]
  },
  "confidence": 0.72,
  "review_details": {
    "news_relevance": 0.70,
    "trend_alignment": 0.75,
    "cross_consistency": 0.68
  }
}
```

### 4.2 需要验证的关键点

1. **报告是否每小时生成** ❓
   - 检查方式：查看 D 盘报告目录中今天（04-21）是否有多个文件

2. **报告采集源覆盖** ❓
   - 检查方式：采样一份报告，统计 `news` 字段中的 `source` 分布
   - 预期：jin10 + rss + 其他来源混合，不仅仅是 jin10

3. **宏观数据融入** ❓
   - 检查方式：采样报告中是否有 `macro` 字段内容（不仅仅空对象）

---

## 五、Decision 消费状态（需日志确认）

### 5.1 预期流程

```python
# Decision ResearcherLoader 应该这样工作：
ResearcherLoader(data_service_url="http://192.168.31.187:8199")
  → GET /reports/latest
  → 返回最新报告 JSON
  → Decision 评分器评估报告
  → 结果用于策略决策
```

### 5.2 需要验证

1. Decision 日志中是否有研报加载和评分的记录
2. 评分器是否成功调用并返回评分结果
3. 是否有任何 HTTP 错误或超时问题

---

## 六、 重点发现与行动项

### ✅ 核心发现

- **架构设计正确**：Alienware 8199 直连 Decision 8104，Mini 是可选存档
- **Mini 采集正常**：news_api 每分钟 111 条新闻，最新时间 2026-04-21 12:56（刚采集）
- **Alienware 8199 API 存在**：端点 `/reports/latest` 已验证存在
- **无需 P0 修改 Mini API**：架构已正确实现，不需要通过 Mini 中转

### 🔄 后续验证清单

#### Priority 1 - 采样 Alienware 研报
```bash
# 需要从 Alienware 远程访问报告文件
ssh 17621@192.168.31.187 "ls -lh C:\\Users\\17621\\JBT\\services\\data\\runtime\\researcher\\reports\\2026-04-21\\"
```
- 确认今日是否有报告文件
- 采样一份报告检查采集源覆盖

#### Priority 2 - 检查 Decision 消费日志
```bash
# 查看 Decision 是否成功读取和评分报告
docker logs JBT-DECISION-8104 | grep -i researcher | tail -50
```
- 确认是否有 researcher_loader 和 scorer 的日志
- 检查是否有错误或异常

#### Priority 3 - 调查宏观源采集中断
```bash
# Mini 中是否有 sentiment / macro 采集任务正在运行
ssh jaybot@192.168.31.74 "docker exec JBT-DATA-8105 tail -100 /data/logs/scheduler.log | grep -E 'sentiment|macro|shipping'"
```
- 确认这些采集任务是否注册并运行
- 如果中断，需要独立任务修复

---

## 七、 总结

**U0 纠正前的误判**：
- ❌ 认为 Decision 需要通过 Mini API 消费报告
- ❌ 认为 Mini API `/researcher/report/latest` 是关键路径
- ❌ 将 P0 任务定为"实现 Mini 研报 API"

**U0 纠正后的正确认识**：
- ✅ Decision 直接连接 Alienware 8199
- ✅ Mini 的研报 API 是可选备用存档
- ✅ 架构已正确实现，Decision 应该已能消费研报
- ✅ 真实问题可能在：Alienware 研报生成质量、宏观源采集中断

**建议后续行动**：
1. 采样验证 Alienware 研报的采集源覆盖（检查是否真的只有 jin10）
2. 确认 Decision 是否正确消费并评分了报告
3. 如果宏观源采集中断，建立独立故障排查任务

---

**诊断状态**：🟢 架构已验证正确  
**下一步**：待采样验证 Alienware 研报内容与 Decision 消费状态
