# TASK-0113 数据研究员 — 通知规范化 + 国际采集源

| 字段 | 值 |
|------|-----|
| 任务ID | TASK-0113 |
| 服务 | data |
| 类型 | 功能增强 |
| 优先级 | P1 |
| 状态 | 已预审，待 Token |
| 创建 | 2026-04-15 Atlas |
| 关联 | TASK-0110 (数据研究员子系统) |

## 需求来源

Jay.S 2026-04-15 指令（二轮修订）：

1. **飞书**用"资讯"类（blue/📈），全中文，**每工作小时发一次**，精炼、有标题有结果有研判
2. **邮件**只收日报，每天**早报（16:00后）+晚报（23:00后）**两封，内容详尽全中文，**必须有来源、重大策略**
3. **国际采集源**现在一起做，做完同步上线
4. 完成所有代码后统一部署 Alienware
5. 所有数据推到 Mini 的 data API，给 Studio 决策端消费

## 设计要点

### 飞书卡片（三类分流）

| 类型 | 飞书模板 | 图标 | 标题格式 | 触发 |
|------|---------|------|---------|------|
| 研究报告 | `blue` 资讯 | 📈 | `📈 [JBT 数据研究员-{segment}报告] {date}` | 每段研究完成 |
| 执行失败 | `orange` P1 | ⚠️ | `⚠️ [JBT 数据研究员-{segment}报警] 执行失败` | 爬虫/LLM 出错 |
| 突发紧急 | `red` P0 | 🚨 | `🚨 [JBT 数据研究员-紧急] {headline}` | 爬虫发现重大突发（政策/黑天鹅） |

- 报警归报警，资讯归资讯，不混发
- 突发紧急单独一条即时推送，不等段结束
- note footer: `JBT 数据研究员 | {timestamp} | Alienware`

### 邮件日报（两封/天）

- **早报**：午间段执行完毕后发送（~11:40），汇总盘前 + 午间两段
- **晚报**：夜盘段执行完毕后发送（~23:15），汇总盘后 + 夜盘两段
- 邮件主题：`[JBT 数据研究员] YYYY-MM-DD 早报/晚报`
- HTML Card 格式，详尽内容：完整市场概览、品种涨跌、爬虫要闻、变化要点、关键建议
- footer: `JBT 数据研究员 | {timestamp} | Alienware`

### 国际采集源（7 个新增）

| 源 ID | 名称 | URL | 模式 | 调度时段 |
|--------|------|-----|------|---------|
| `cme_advisory` | CME Group 公告 | cmegroup.com/market-data/advisories | code | 盘前 |
| `kitco_gold` | Kitco 贵金属 | kitco.com/news | code | 盘前/午间/盘后 |
| `oilprice_com` | OilPrice 能源 | oilprice.com/latest-energy-news | code | 盘前/午间/盘后 |
| `mining_com` | Mining 矿业 | mining.com/news | code | 盘前/盘后 |
| `investing_commodities` | Investing 大宗商品 | investing.com/commodities | code | 全四段 |
| `fed_releases` | 美联储公告 | federalreserve.gov/newsevents | code | 盘前 |
| `reuters_commodities` | 路透社大宗商品 | reuters.com/markets/commodities | code | 全四段 |

## 文件清单（4 批 13 文件）

### Batch A — 通知规范化（5 文件）

| # | 文件 | 动作 | 说明 |
|---|------|------|------|
| 1 | `services/data/src/researcher/notifier.py` | MODIFY | 飞书卡片改 blue 资讯模板 |
| 2 | `services/data/src/researcher/notify/card_templates.py` | MODIFY | 统一标题 blue + 详尽邮件日报 HTML |
| 3 | `services/data/src/researcher/notify/daily_digest.py` | MODIFY | 改造为早报/晚报两种模式 |
| 4 | `services/data/src/researcher/notify/email_sender.py` | MODIFY | 中文主题 |
| 5 | `services/data/src/researcher/notify/__init__.py` | MODIFY | 导出更新 |

### Batch B — 调度与配置（2 文件）

| # | 文件 | 动作 | 说明 |
|---|------|------|------|
| 6 | `services/data/src/researcher/config.py` | MODIFY | 添加早报/晚报时间配置 |
| 7 | `services/data/src/researcher/scheduler.py` | MODIFY | 早报/晚报邮件调度钩子 |

### Batch C — 国际采集源（3 文件）

| # | 文件 | 动作 | 说明 |
|---|------|------|------|
| 8 | `services/data/configs/researcher_sources.yaml` | MODIFY | 添加 7 个国际源 |
| 9 | `services/data/src/researcher/crawler/parsers/international.py` | NEW | 7 个国际源 lxml 解析器 |
| 10 | `services/data/src/researcher/crawler/parsers/__init__.py` | MODIFY | 注册国际解析器 |

### Batch D — 测试（3 文件）

| # | 文件 | 动作 | 说明 |
|---|------|------|------|
| 11 | `services/data/tests/test_researcher_international.py` | NEW | 国际源解析器测试 |
| 12 | `services/data/tests/test_researcher_daily_mail.py` | NEW | 早报/晚报测试 |
| 13 | `services/data/tests/test_researcher_card_blue.py` | NEW | 卡片 blue 格式测试 |

## 验收标准

1. `pytest services/data/tests/test_researcher_*.py -v` 全部通过
2. 飞书卡片用 blue 模板，标题含"JBT 数据研究员"
3. 邮件日报 HTML 详尽、全中文、含完整市场分析
4. 国际源解析器能正确处理各站点 HTML 结构
5. 早报/晚报调度逻辑正确（午间后/夜盘后）
