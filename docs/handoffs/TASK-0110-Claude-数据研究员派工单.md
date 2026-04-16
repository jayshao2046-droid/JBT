# TASK-0110 Claude 派工单 — 数据研究员子系统

【创建】2026-04-15
【任务文件】`docs/tasks/TASK-0110-data-researcher-数据研究员子系统.md`
【预审文件】`docs/reviews/TASK-0110-review.md`
【锁控文件】`docs/locks/TASK-0110-lock.md`
【执行 Agent】Claude-Code
【执行策略】A → B → C → C2 → D → E 一次性全批执行，全部完成后统一核验。不必等单批验证再进入下批，但代码依赖顺序仍为 A→B→C→C2→D→E。

---

## 项目背景

在 data 服务内新增"数据研究员"子系统：
- **设备**：Alienware（192.168.31.223），RTX 2070 8GB，qwen3:14b via Ollama (http://192.168.31.223:11434)
- **数据源**：Mini（192.168.31.76:8105）全量采集数据 + 双模式爬虫
- **产出**：四段制双格式报告（JSON 决策版 + Markdown Jay 版）
- **消费者**：决策端（Studio 192.168.31.142:8104）通过 `/api/v1/researcher/report/latest` 读取

## 关键技术约定

### Alienware Ollama 调用
```python
import httpx
OLLAMA_URL = "http://192.168.31.223:11434"
resp = httpx.post(f"{OLLAMA_URL}/api/generate", json={
    "model": "qwen3:14b",
    "prompt": "...",
    "stream": False,
    "options": {"temperature": 0.3, "num_ctx": 8192}
}, timeout=120.0)
result = resp.json()["response"]
```

### Mini 数据 API 读取（暂存区用）
```python
DATA_API_URL = "http://192.168.31.76:8105"
# 获取 K 线数据
resp = httpx.get(f"{DATA_API_URL}/api/v1/bars", params={...})
# 获取预研上下文
resp = httpx.get(f"{DATA_API_URL}/api/v1/context/daily")
```

### 四段调度时间
| 时段 | 触发时间 | 说明 |
|------|---------|------|
| 盘前 | 08:30 | 分析隔夜数据+外盘 |
| 午间 | 11:35 | 上午盘汇总 |
| 盘后 | 15:20 | 全天总结 |
| 夜盘 | 23:10 + 02:40 | 夜盘收盘汇总（次日） |

### 研究范围
- 期货：35 品种（全 continuous 合约）
- 股票：Top100 + 自选池 30 只 = 130 只

### 爬虫双模式
- **代码模式**：httpx + lxml，用于结构化 API/RSS
- **浏览器模式**：Playwright headless Chromium，用于反爬严格的站点
- 每个采集源在配置中指定 `mode: "code"` 或 `mode: "browser"`

### 现有参照代码
- 预读系统：`services/data/src/scheduler/preread_generator.py`（规则聚合，四角色上下文）
- 调度注册：`services/data/src/scheduler/data_scheduler.py`（APScheduler add_job 模式）
- 通知分发：`services/data/src/notify/dispatcher.py`（NotifyType 枚举 + 飞书/邮件路由）
- context API：`services/data/src/api/routes/context_route.py`（FastAPI router 模式）

### 飞书通知颜色
- 研究报告完成 → `turquoise`（通知类）
- 研究报告失败 → `orange`（P1 报警类）

### 决策端对接 API 契约
详见任务文件"data 端研究员 API 契约"章节。核心端点：
- `GET /api/v1/researcher/report/latest` — 决策端拉取最新报告
- `GET /api/v1/researcher/report/{date}/{segment}` — 指定日期+时段
- `GET /api/v1/researcher/status` — 子系统状态
- `POST /api/v1/researcher/trigger` — 手动触发

---

## 批次 A — 增量读取 + 暂存区 + summarizer 骨架（8 文件）

**Token ID**：`tok-d581b218-e5e0-457b-8787-1d98ca680503`

### 文件清单
| # | 文件 | 操作 |
|---|------|------|
| 1 | `services/data/src/researcher/__init__.py` | 新建 |
| 2 | `services/data/src/researcher/staging.py` | 新建 |
| 3 | `services/data/src/researcher/summarizer.py` | 新建 |
| 4 | `services/data/src/researcher/reporter.py` | 新建 |
| 5 | `services/data/src/researcher/models.py` | 新建 |
| 6 | `services/data/src/researcher/config.py` | 新建 |
| 7 | `services/data/tests/test_researcher_staging.py` | 新建 |
| 8 | `services/data/tests/test_researcher_reporter.py` | 新建 |

### 核心要求

**staging.py — 暂存区管理**
- 从 Mini data API 增量拉取数据（按品种+时间水位追踪）
- 本地 SQLite 或 JSON 记录每个品种的 `last_read_ts`
- 拉取后存入暂存区（`runtime/researcher/staging/`）
- 提供 `get_incremental(symbols, since)` 接口

**summarizer.py — LLM 归纳**
- 调用 Alienware Ollama qwen3:14b
- prompt 分两部分：当期增量数据 + 上期摘要（变化对比）
- 输出结构化 JSON（trend/confidence/key_factors）
- 超时保护 120s，失败降级为"无法归纳"

**reporter.py — 双格式报告**
- JSON 决策版：`futures_summary` + `stocks_summary` + `crawler_stats`
- Markdown Jay 版：飞书卡片友好格式
- 报告存储到 `runtime/researcher/reports/{date}/{segment}.json`
- 保留上期 `previous_report_id` 用于变化追踪

**models.py — 数据模型**
- `ResearchReport`：报告主体
- `StagingRecord`：暂存区记录
- `SourceConfig`：采集源配置
- `SymbolResearch`：品种级研究结果

**config.py — 配置管理**
- 品种列表（35 期货 + 130 股票）
- 时段定义（盘前/午间/盘后/夜盘）
- Ollama 参数（url/model/temperature/num_ctx/timeout）
- 资源监控阈值（GPU >90% / 延迟 >200ms 暂停）

### 验证
```bash
cd /Users/jayshao/JBT
pytest services/data/tests/test_researcher_staging.py services/data/tests/test_researcher_reporter.py -q
```

---

## 批次 B — 爬虫引擎 + 预置解析器（8 文件）

**Token ID**：`tok-e3b7b3c5-db1e-4cb5-9eab-c42bfe313c92`

### 文件清单
| # | 文件 | 操作 |
|---|------|------|
| 1 | `services/data/src/researcher/crawler/__init__.py` | 新建 |
| 2 | `services/data/src/researcher/crawler/engine.py` | 新建 |
| 3 | `services/data/src/researcher/crawler/source_registry.py` | 新建 |
| 4 | `services/data/src/researcher/crawler/parsers/__init__.py` | 新建 |
| 5 | `services/data/src/researcher/crawler/parsers/generic.py` | 新建 |
| 6 | `services/data/src/researcher/crawler/parsers/futures.py` | 新建 |
| 7 | `services/data/src/researcher/crawler/anti_detect.py` | 新建 |
| 8 | `services/data/tests/test_researcher_crawler.py` | 新建 |

### 核心要求

**engine.py — 双模式引擎**
- `CodeCrawler`：httpx + lxml，适用于结构化 API / RSS
- `BrowserCrawler`：Playwright headless Chromium，适用于动态页面
- 统一 `CrawlResult` 输出：`{url, title, content, published_at, source_id}`
- 并发控制：代码模式 max 5 并发，浏览器模式 max 2
- 请求间隔可配（默认 2s 代码 / 5s 浏览器）

**source_registry.py — 采集源注册表**
- 三层配置：代码定义（默认） → YAML 覆盖 → 数据库热配（最高优先）
- 每个源：`{source_id, name, url_pattern, mode, parser, schedule, enabled}`
- `get_active_sources(segment)` — 按时段过滤活跃源

**parsers/futures.py — 期货专用解析器**
- 东方财富期货频道
- 金十数据快讯
- 新浪财经期货
- 各交易所公告（上期所/大商所/郑商所/中金所）

**anti_detect.py — 反检测**
- User-Agent 轮换池（≥20 个 UA）
- 请求间隔随机化（base ± 30%）
- Playwright 指纹特征去除（webdriver 标记等）
- 遇到 429/403 自动退避（指数退避 3 次后跳过该源）

### 验证
```bash
pytest services/data/tests/test_researcher_crawler.py -q
```

---

## 批次 C — 四段调度 + 通知推送（5 文件, 含 2 修改）

**Token ID**：`tok-4ad3a529-e41c-4b47-b02b-d84e3ec3bc88`

### 文件清单
| # | 文件 | 操作 |
|---|------|------|
| 1 | `services/data/src/researcher/scheduler.py` | 新建 |
| 2 | `services/data/src/researcher/notifier.py` | 新建 |
| 3 | `services/data/src/scheduler/data_scheduler.py` | **修改** |
| 4 | `services/data/src/notify/dispatcher.py` | **修改** |
| 5 | `services/data/tests/test_researcher_scheduler.py` | 新建 |

### 核心要求

**scheduler.py — 四段调度器**
- 四个 cron job：08:30 / 11:35 / 15:20 / 23:10（夜盘加 02:40 次日）
- 每次执行流程：暂存区增量读取 → 爬虫采集 → summarizer 归纳 → reporter 生成 → notifier 推送
- Alienware 资源监控：GPU > 90% 或 sim-trading 延迟 > 200ms 时暂停研究
- 执行超时保护（单次 ≤15 分钟）

**notifier.py — 推送**
- 飞书卡片（Jay 版 Markdown）→ 使用 `turquoise` 模板
- 决策版 JSON → 写入 `runtime/researcher/reports/` + 通过 API 可查
- 失败告警 → 使用 `orange` 模板

**data_scheduler.py 修改**
- 在 `register_jobs()` 中新增 researcher 四段 job 注册
- 参照现有 preread job 模式

**dispatcher.py 修改**
- NotifyType 枚举新增 `RESEARCH_REPORT_DONE` / `RESEARCH_REPORT_FAIL`
- 对应路由到飞书 + 邮件

### 验证
```bash
pytest services/data/tests/test_researcher_scheduler.py -q
```

---

## 批次 C2 — 研究员独立通知体系（5 文件 + 1 测试，Alienware 独立飞书+邮件）

**Token ID**：`tok-597e842c-f468-42ed-9b49-b8e069372ed2`

### 设计原则

研究员通知体系**完全独立于** data 端（Mini）和 sim-trading（Alienware）的现有通知系统：
- **独立 webhook**：使用 `RESEARCHER_FEISHU_WEBHOOK_URL`，不复用 data/sim 的报警群/交易群/资讯群
- **独立邮件**：使用 `RESEARCHER_EMAIL_*` 系列环境变量，不复用 data 端 SMTP 配置
- **独立卡片模板**：研究员专用飞书卡片和邮件 HTML，与 data 端 `card_templates.py` 互不影响
- **独立每日日报**：夜盘收盘后（约 02:50）自动汇总当日全部四段的执行/分析/建议

### 环境变量（Alienware `.env` 新增）

```env
# 研究员独立飞书 — 单独建一个飞书群/机器人
RESEARCHER_FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx-researcher
# 研究员独立邮件
RESEARCHER_EMAIL_SMTP_HOST=smtp.qq.com
RESEARCHER_EMAIL_SMTP_PORT=465
RESEARCHER_EMAIL_SENDER=researcher@xxx.com
RESEARCHER_EMAIL_PASSWORD=xxx
RESEARCHER_EMAIL_RECIPIENTS=jay@xxx.com
```

### 文件清单
| # | 文件 | 操作 |
|---|------|------|
| 1 | `services/data/src/researcher/notify/__init__.py` | 新建 |
| 2 | `services/data/src/researcher/notify/feishu_sender.py` | 新建 |
| 3 | `services/data/src/researcher/notify/email_sender.py` | 新建 |
| 4 | `services/data/src/researcher/notify/card_templates.py` | 新建 |
| 5 | `services/data/src/researcher/notify/daily_digest.py` | 新建 |
| 6 | `services/data/tests/test_researcher_notify.py` | 新建 |

### 核心要求

#### feishu_sender.py — 独立飞书发送器

- 只读 `RESEARCHER_FEISHU_WEBHOOK_URL`，与 data 端 `FEISHU_ALERT/TRADE/INFO_WEBHOOK_URL` 无关
- 使用 `msg_type: "interactive"` 卡片格式（遵循 JBT 统一标准）
- 发送失败时记录到本地 `runtime/researcher/logs/notify_failures.jsonl`
- 不走 data 端 `dispatcher.py` 的三群路由

#### email_sender.py — 独立邮件发送器

- 只读 `RESEARCHER_EMAIL_*` 环境变量
- 使用 JBT 统一 HTML Card 格式
- SSL/TLS 加密
- 发送失败时降级为本地日志

#### card_templates.py — 研究员专用模板（飞书+邮件）

**飞书卡片类型（6 种）：**

| 卡片 | 颜色 | 触发时机 | 内容 |
|------|------|---------|------|
| `segment_start_card` | `blue` 📈 | 每段开始执行 | 时段名 / 开始时间 / 计划品种数 / 计划采集源数 |
| `segment_done_card` | `turquoise` 📣 | 每段完成 | 品种覆盖 / 趋势变化 / 关键发现 / 耗时 / 采集统计 |
| `segment_fail_card` | `orange` ⚠️ | 每段失败 | 失败原因 / 影响范围 / 降级状态 |
| `recommendation_card` | `blue` 📈 | 随 segment_done 紧跟发送 | Top3 品种建议 / 风险提示 / 关注事项 |
| `daily_digest_card` | `turquoise` 📣 | 夜盘后 ~02:50 | 全天汇总（见下方详细设计） |
| `resource_warning_card` | `orange` ⚠️ | GPU>90% 或延迟>200ms | Alienware 资源告警 / 暂停研究通知 |

**飞书 `segment_done_card` 结构：**
```
header: "📣 [RESEARCHER-NOTIFY] 盘前研究完成"  template: turquoise
elements:
  - div(lark_md): "**品种覆盖** 期货 35 / 股票 130"
  - div(lark_md): "**趋势变化** 螺纹钢 偏多→偏空 | 沪铜 持平"
  - div(lark_md): "**爬虫采集** 12源 48篇 | 失败: 金十(429)"
  - hr
  - div(lark_md): "**关键发现**\n• 螺纹钢库存连续3周增加\n• 原油受中东局势影响偏强"
  - hr
  - note: "JBT Researcher | 2026-04-15 08:45:00 | 耗时 12m30s"
```

**飞书 `recommendation_card` 结构：**
```
header: "📈 [RESEARCHER-INFO] 盘前研究建议"  template: blue
elements:
  - div(lark_md): "**Top3 关注品种**"
  - div(lark_md): "1️⃣ 螺纹钢(rb) — 偏空 0.72 — 库存压力+需求放缓"
  - div(lark_md): "2️⃣ 原油(sc) — 偏多 0.68 — 中东局势+库存下降"
  - div(lark_md): "3️⃣ 沪铜(cu) — 观望 0.51 — 多空因素均衡"
  - hr
  - div(lark_md): "**风险提示**\n• 螺纹钢今日有交割月换月\n• 关注20:30美国CPI数据"
  - hr
  - note: "JBT Researcher | 2026-04-15 08:45:05"
```

**邮件 HTML 结构：** 遵循 JBT 统一 Card 格式，参照 `services/data/src/notify/email_notify.py` 的 `_build_event_html` 风格。

#### daily_digest.py — 每日综合日报生成器

**触发时间：** 夜盘收盘后约 02:50（或最后一段完成后 10 分钟）

**日报内容结构（飞书长卡片 + 邮件 HTML）：**

```
═══════════════════════════════════════════════════
📣 [RESEARCHER-NOTIFY] 2026-04-15 研究员每日总结
═══════════════════════════════════════════════════

📋 执行概况
┌──────┬──────┬──────┬──────┬──────┐
│ 时段 │ 状态 │ 耗时 │ 品种 │ 采集 │
├──────┼──────┼──────┼──────┼──────┤
│ 盘前 │ ✅   │ 12m  │ 165  │ 48篇 │
│ 午间 │ ✅   │ 8m   │ 165  │ 32篇 │
│ 盘后 │ ✅   │ 15m  │ 165  │ 55篇 │
│ 夜盘 │ ✅   │ 10m  │ 35   │ 28篇 │
└──────┴──────┴──────┴──────┴──────┘
合计: 4段全部成功 | LLM调用 12次 | 爬虫采集 163篇

📊 今日看了什么
- 期货品种: 35个全覆盖（rb/cu/sc/...）
- 股票品种: Top100 + 自选30 = 130只
- 爬虫源: 东财/金十/新浪/上期所/大商所/郑商所/财联社
  成功率: 11/12 (91.7%) | 金十午间429被限流
- K线数据: 增量读取 12,450 bars
- 预研上下文: 已整合 preread 四角色摘要

📈 今日总结了什么
- 期货整体: 黑色系偏空（库存压力），能化偏多（中东+库存）
- 股票整体: 大盘震荡，科技板块领涨，地产持续承压
- 关键变化:
  • 螺纹钢(rb): 盘前偏多 → 盘后偏空（午间库存数据发布）
  • 原油(sc): 全天偏多不变（中东局势持续发酵）
  • 沪铜(cu): 午间偏多 → 盘后观望（晚间美CPI预期）

💡 今日建议
- 重点关注: 螺纹钢空头机会（库存拐点已确认）
- 风险警示: 原油多头注意止损（若美CPI超预期可能回落）
- 明日关注: 08:30 中国GDP / 20:30 美国零售数据
- 策略建议:
  • rb: 可考虑空单轻仓入场，止损 3600
  • sc: 持有多单不加仓，观察美CPI后再定
  • 股票: 科技ETF可关注回调买点

🖥️ Alienware 资源
- GPU 平均占用: 62% (峰值 85%)
- 内存: 14.2/16 GB
- sim-trading 延迟: avg 12ms (无影响)
- 研究暂停次数: 0

═══════════════════════════════════════════════════
JBT Researcher | 2026-04-15 02:50:00 | Alienware
═══════════════════════════════════════════════════
```

**日报数据来源：**
- 从 `runtime/researcher/reports/{date}/` 读取当日所有时段报告
- 从 `runtime/researcher/logs/execution_{date}.jsonl` 读取执行日志
- 从 `runtime/researcher/staging/` 读取增量统计
- 对比各时段的 `change_highlights` 提取趋势变化
- 资源数据从 `scheduler.py` 的监控指标获取

**日报实现要点：**
```python
class DailyDigestGenerator:
    def generate(self, date: str) -> tuple[dict, str]:
        """生成每日总结。返回 (飞书卡片payload, 邮件HTML)。"""
        segments = self._load_all_segments(date)     # 加载四段报告
        exec_logs = self._load_execution_logs(date)  # 加载执行日志
        
        digest = {
            "execution_summary": self._build_execution_table(exec_logs),
            "what_reviewed": self._build_review_summary(segments),
            "what_summarized": self._build_analysis_summary(segments),
            "recommendations": self._build_recommendations(segments),
            "resource_stats": self._build_resource_stats(exec_logs),
        }
        
        feishu_card = self._render_feishu_card(digest)
        email_html = self._render_email_html(digest)
        return feishu_card, email_html
```

### Batch C2 与 C 的关系

- C 批的 `notifier.py` 负责调用 C2 的独立发送器，不走 data 端 `dispatcher.py`
- C 批的 `scheduler.py` 在每段完成后调用 `notifier.py` → `feishu_sender` + `email_sender`
- C 批的 `scheduler.py` 在夜盘收盘后调用 `daily_digest.py` 生成日报
- C 批修改 `dispatcher.py` 只是新增 NotifyType 枚举值（用于状态查询），实际推送不经过 dispatcher

### 验证
```bash
pytest services/data/tests/test_researcher_notify.py -q
```

---

## 批次 D — API 接口 + 采集源配置（4 文件, 含 1 修改）

**Token ID**：`tok-1346b99a-014b-42e0-b218-3c8dd459a0d9`

### 文件清单
| # | 文件 | 操作 |
|---|------|------|
| 1 | `services/data/src/api/routes/researcher_route.py` | 新建 |
| 2 | `services/data/src/main.py` | **修改** |
| 3 | `services/data/tests/test_researcher_api.py` | 新建 |
| 4 | `services/data/configs/researcher_sources.yaml` | 新建 |

### 核心要求

**researcher_route.py — REST API（9 个端点）**
详见任务文件"data 端研究员 API 契约"章节。必须实现：
- `GET /api/v1/researcher/report/latest`
- `GET /api/v1/researcher/report/{date}`
- `GET /api/v1/researcher/report/{date}/{segment}`
- `GET /api/v1/researcher/status`
- `POST /api/v1/researcher/trigger`
- `GET /api/v1/researcher/sources`
- `POST /api/v1/researcher/sources`
- `PUT /api/v1/researcher/sources/{source_id}`
- `DELETE /api/v1/researcher/sources/{source_id}`

**main.py 修改**
- 注册 researcher_route router，前缀保持一致

**researcher_sources.yaml — 预置采集源**
- 至少预置 6 个源：东财期货/金十/新浪期货/各交易所公告/同花顺/财联社
- 每个源包含：source_id / name / url_pattern / mode / parser / schedule / enabled

### 验证
```bash
pytest services/data/tests/test_researcher_api.py -q
```

---

## 批次 E — 看板研究员控制台（4 文件, dashboard 端）

**Token ID**：`tok-b2e48251-340d-4f7b-a84b-287058720fa8`

### 文件清单
| # | 文件 | 操作 |
|---|------|------|
| 1 | `services/dashboard/dashboard_web/app/data/researcher/page.tsx` | 新建 |
| 2 | `services/dashboard/dashboard_web/app/data/researcher/components/source-manager.tsx` | 新建 |
| 3 | `services/dashboard/dashboard_web/app/data/researcher/components/report-viewer.tsx` | 新建 |
| 4 | `services/dashboard/dashboard_web/app/data/researcher/components/resource-monitor.tsx` | 新建 |

### 核心要求

**page.tsx — 研究员控制台主页**
- 三区布局：左侧采集源管理 / 右上报告查看 / 右下资源监控
- 调用 data:8105 的 researcher API

**source-manager.tsx — 采集源管理**
- 源列表 CRUD（启用/禁用/新增/编辑/删除）
- 显示每个源最后采集状态 + 成功率

**report-viewer.tsx — 报告查看**
- 按日期+时段浏览报告
- JSON 决策版和 Markdown Jay 版切换
- 品种级详情展开

**resource-monitor.tsx — 资源监控**
- Alienware GPU/CPU/内存实时状态
- sim-trading 延迟监控
- 研究员调度状态（下次执行时间 / 上次结果）

### 验证
```bash
cd services/dashboard/dashboard_web && pnpm build
```

---

## 搜索/情报补充方案最终选型（2026-04-15 冻结）

**最终选型：方案 C（混合路由，搜索在 data 层缓存，不直连 Ollama）**

### 三方案对比与排除理由

| 方案 | 核心机制 | 结论 |
|------|---------|------|
| A：Ollama Tool Calling | qwen3:14b 挂 web_search function，LLM 决定调用 | ❌ 排除 |
| B：qwen-plus 原生联网 | DashScope `enable_search: true` | ❌ 排除 |
| C：混合路由（搜索在 data 层） | 爬虫采集 → staging → 注入 context | ✅ 采纳 |

**方案 A 排除**：
- TASK-0110 B 批双模式爬虫引擎（`crawler/engine.py`）已实现等价采集能力，无需额外 tool calling 层
- Ollama tool calling 稳定性不如定时爬虫 + staging 结构化注入
- 让 LLM "决定是否搜索"与已冻结的"搜索只作排除项增强"口径不符（搜索需要可控、确定性触发）

**方案 B 排除**：
- 违背 `总项目经理调度提示词.md` 冻结口径："Alienware 只保留 `qwen3:14b`"，不得引入 DashScope 在线模型
- 期货持仓/成交等敏感数据不得过境阿里云
- 搜索结果 context 增加 30~50% token 量且不可控

**方案 C 采纳**：
- 与 TASK-0110 已批准架构完全一致：B 批 `crawler/` 模块本身就是 SearchCollector 角色
- 数据流：爬虫采集（B 批）→ staging 暂存区（A 批）→ summarizer prompt 注入（A 批 `summarizer.py`）→ qwen3:14b 生成报告
- 盘中 Studio 侧 phi4/deepcoder 不联网，只读当期报告 JSON，搜索信息已被研究员预消化
- 完全本地控制，Alienware GPU 推理，零额外云费用

### 实现约束（硬冻结）

1. **搜索结果只作排除项增强**，不得作为无条件加分信号
2. **爬虫采集结果以结构化 JSON 缓存进 staging 暂存区**，不直连 Ollama tool calling
3. **不引入任何在线模型**（DashScope/Tavily/Brave 付费 API 均不引入）
4. 爬虫采集时段：**夜间/盘前**为主，盘中仅被动读缓存，不实时爬取（保护 Alienware 盘中交易资源）
5. 爬虫失败时研究报告**静默降级**（只用 Mini 数据分析），不因爬虫出错中断四段报告

---

## 后续关联任务提示

TASK-0110 完成后，需建立 TASK-0111（决策端对接）：
- 新建 `services/decision/src/llm/researcher_loader.py`
- 修改 `services/decision/src/llm/pipeline.py`
- 新建 `services/decision/tests/test_researcher_loader.py`
- 详见任务文件"决策端对接指南"章节
