# TASK-0110 — data 研究员子系统（Alienware qwen3:14b + 双模式爬虫 + 四段报告）

【创建】2026-04-15
【服务归属】`services/data/`（子模块 `src/researcher/`）
【执行 Agent】Claude-Code
【状态】建档完成，待签发

## 任务概述

在 data 服务内新增"数据研究员"子系统，运行在 Alienware（192.168.31.187）上，通过 qwen3:14b 对 Mini 采集的全量数据做**增量预读归纳**，同时通过**双模式爬虫**（代码模式 + 浏览器模式）采集期货/股票相关资讯，最终生成**四段制双格式报告**推送给决策端和 Jay.S。

## 需求来源

Jay.S 2026-04-15 确认：
1. 以期货 35 品种为主，股票（Top100 + 自选池 30 只）为辅
2. 增量读取 + 暂存区，不重读旧数据；写摘要时回看上期做变化对比
3. 爬虫以期货为主（35 品种突发新闻/行业信息），结合外盘交叉验证
4. 四段制：盘前/午间/盘后/夜盘收盘
5. 爬虫双模式：代码模式（httpx）+ 浏览器模式（Playwright），配置驱动
6. 产出两份报告：决策格式（JSON 结构化）+ Jay 个人格式（Markdown/飞书）
7. 先盘中测试一周监控 Alienware 资源，影响交易则暂停盘中
8. 每份报告可含图表数据（持仓/仓单类时间序列）
9. 看板后续增加研究员控制台（采集源管理/动态/报告查看）
10. 归属 `services/data/`，不独立建服务

## 分批计划

### 批次 A — 增量读取 + 暂存区 + summarizer 骨架（P1，8 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/__init__.py` | 新建 | 模块入口 |
| `services/data/src/researcher/staging.py` | 新建 | 暂存区管理：增量标记、水位追踪、数据拉取 |
| `services/data/src/researcher/summarizer.py` | 新建 | qwen3 Ollama 调用封装：prompt 构建、token 限制、历史对比 |
| `services/data/src/researcher/reporter.py` | 新建 | 双格式报告生成：JSON 决策版 + Markdown Jay版 |
| `services/data/src/researcher/models.py` | 新建 | 数据模型：ResearchReport / StagingRecord / SourceConfig |
| `services/data/src/researcher/config.py` | 新建 | 配置管理：品种列表、时段定义、Ollama 参数 |
| `services/data/tests/test_researcher_staging.py` | 新建 | 暂存区 + summarizer 测试 |
| `services/data/tests/test_researcher_reporter.py` | 新建 | 报告生成测试 |

### 批次 B — 爬虫引擎 + 预置解析器（P1，8 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/crawler/__init__.py` | 新建 | 爬虫子模块 |
| `services/data/src/researcher/crawler/engine.py` | 新建 | 双模式引擎：代码模式(httpx) + 浏览器模式(Playwright) |
| `services/data/src/researcher/crawler/source_registry.py` | 新建 | 采集源注册表：从数据库/YAML 加载配置 |
| `services/data/src/researcher/crawler/parsers/__init__.py` | 新建 | 解析器注册 |
| `services/data/src/researcher/crawler/parsers/generic.py` | 新建 | 通用解析器：article_list / rss / json_api |
| `services/data/src/researcher/crawler/parsers/futures.py` | 新建 | 期货专用解析器：东财/金十/新浪 |
| `services/data/src/researcher/crawler/anti_detect.py` | 新建 | 反检测：UA 轮换、请求间隔、Playwright 指纹 |
| `services/data/tests/test_researcher_crawler.py` | 新建 | 爬虫引擎测试 |

### 批次 C — 四段调度 + 通知推送（5 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/scheduler.py` | 新建 | 四段调度器：盘前/午间/盘后/夜盘，含 Alienware 资源监控 |
| `services/data/src/researcher/notifier.py` | 新建 | 推送：飞书卡片(Jay版) + Mini data API(决策版) |
| `services/data/src/scheduler/data_scheduler.py` | 修改 | 注册 researcher 四段 job |
| `services/data/src/notify/dispatcher.py` | 修改 | 新增 RESEARCH_REPORT_DONE / RESEARCH_REPORT_FAIL 通知类型 |
| `services/data/tests/test_researcher_scheduler.py` | 新建 | 调度 + 通知测试 |

### 批次 C2 — 研究员独立通知体系（5 文件，Alienware 独立飞书+邮件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/notify/__init__.py` | 新建 | 通知子模块入口 |
| `services/data/src/researcher/notify/feishu_sender.py` | 新建 | 独立飞书发送器（独立 webhook，不共享 data/sim 的群） |
| `services/data/src/researcher/notify/email_sender.py` | 新建 | 独立邮件发送器（独立 SMTP 配置） |
| `services/data/src/researcher/notify/card_templates.py` | 新建 | 研究员专用卡片/邮件模板（四段报告+每日总结+执行日志） |
| `services/data/src/researcher/notify/daily_digest.py` | 新建 | 每日综合日报生成器（汇总当日所有段落的执行/分析/建议） |

### 批次 D — API 接口 + 采集源 CRUD（P1，4 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/api/routes/researcher_route.py` | 新建 | REST API：报告查询 / 采集源 CRUD / 状态 / 手动触发 |
| `services/data/src/main.py` | 修改 | 注册 researcher_route |
| `services/data/tests/test_researcher_api.py` | 新建 | API 端点测试 |
| `services/data/configs/researcher_sources.yaml` | 新建 | 预置采集源配置（可被数据库覆盖） |

### 批次 E — 看板研究员控制台（P1，4 文件，dashboard 端）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/dashboard/dashboard_web/app/data/researcher/page.tsx` | 新建 | 研究员控制台主页 |
| `services/dashboard/dashboard_web/app/data/researcher/components/source-manager.tsx` | 新建 | 采集源管理组件 |
| `services/dashboard/dashboard_web/app/data/researcher/components/report-viewer.tsx` | 新建 | 报告查看组件 |
| `services/dashboard/dashboard_web/app/data/researcher/components/resource-monitor.tsx` | 新建 | 资源监控组件 |

## 依赖链

```
A（骨架） → B（爬虫） → C（调度+推送） → C2（独立通知体系） → D（API） → E（看板）
```

## 验收标准

- A 批：`pytest services/data/tests/test_researcher_staging.py test_researcher_reporter.py -q` 全通过
- B 批：`pytest services/data/tests/test_researcher_crawler.py -q` 全通过
- C 批：`pytest services/data/tests/test_researcher_scheduler.py -q` 全通过
- C2 批：`pytest services/data/tests/test_researcher_notify.py -q` 全通过
- D 批：`pytest services/data/tests/test_researcher_api.py -q` 全通过
- E 批：`pnpm build` 通过，页面可访问
- 全量：Alienware 上端到端跑一次四段报告，飞书收到 Jay 版，Mini data API 可查决策版

---

## data 端研究员 API 契约（Batch D `researcher_route.py` 必须实现）

### 端点一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/researcher/report/latest` | 获取最新一期研究员报告（JSON 决策版） |
| GET | `/api/v1/researcher/report/{date}` | 获取指定日期的研究员报告列表 |
| GET | `/api/v1/researcher/report/{date}/{segment}` | 获取指定日期+时段的报告 |
| GET | `/api/v1/researcher/status` | 研究员子系统状态（调度/资源/上次运行） |
| POST | `/api/v1/researcher/trigger` | 手动触发一次指定时段的研究 |
| GET | `/api/v1/researcher/sources` | 获取采集源列表 |
| POST | `/api/v1/researcher/sources` | 新增采集源 |
| PUT | `/api/v1/researcher/sources/{source_id}` | 更新采集源配置 |
| DELETE | `/api/v1/researcher/sources/{source_id}` | 删除采集源 |

### `/api/v1/researcher/report/latest` 响应格式（决策版 JSON）

```json
{
  "report_id": "RPT-20260415-盘前-001",
  "date": "2026-04-15",
  "segment": "盘前",
  "generated_at": "2026-04-15T08:45:00+08:00",
  "model": "qwen3:14b",
  "futures_summary": {
    "symbols_covered": 35,
    "market_overview": "...",
    "symbols": {
      "KQ.m@SHFE.rb": {
        "trend": "偏空",
        "confidence": 0.72,
        "key_factors": ["库存增加", "需求放缓"],
        "overnight_context": "...",
        "news_highlights": ["..."],
        "position_change": { "long": -1200, "short": +800 }
      }
    }
  },
  "stocks_summary": {
    "symbols_covered": 130,
    "market_overview": "...",
    "top_movers": [ ... ],
    "sector_rotation": { ... }
  },
  "crawler_stats": {
    "sources_crawled": 12,
    "articles_processed": 48,
    "failed_sources": ["..."]
  },
  "previous_report_id": "RPT-20260414-夜盘-001",
  "change_highlights": ["螺纹钢从偏多转偏空", "..."]
}
```

### `/api/v1/researcher/report/{date}` 响应格式

```json
{
  "date": "2026-04-15",
  "segments": [
    { "segment": "盘前",  "report_id": "RPT-20260415-盘前-001",  "generated_at": "..." },
    { "segment": "午间",  "report_id": "RPT-20260415-午间-001",  "generated_at": "..." }
  ]
}
```

---

## 决策端对接指南

### 现有模式（参照）

决策端目前通过 `src/llm/context_loader.py` 中的 `DailyContextLoader` 读取预研上下文：

```python
# services/decision/src/llm/context_loader.py
DATA_API_URL = os.getenv("DATA_API_URL", "http://localhost:8105")  # → Mini data:8105
url = f"{DATA_API_URL}/api/v1/context/daily"                      # preread 摘要
```

这是 21:00 一次性的规则聚合。**研究员报告是四段制 + LLM 归纳 + 爬虫情报，独立于 preread。**

### 决策端需要的对接变更（后续关联任务，非 TASK-0110 范围）

决策端需新建一个 `ResearcherReportLoader`，模式与 `DailyContextLoader` 一致：

| 项目 | 值 |
|------|------|
| 新建文件 | `services/decision/src/llm/researcher_loader.py` |
| Base URL | 复用 `DATA_API_URL`（同一 data:8105 服务） |
| 端点 | `/api/v1/researcher/report/latest` |
| TTL | 建议 2 小时（比 preread 的 8h 短，因为四段更新更频繁） |
| 降级 | 返回 None → LLM pipeline 跳过研究员上下文（与 preread 降级一致） |
| 集成点 | `src/llm/pipeline.py` 的 prompt 构建阶段注入 `futures_summary` |

```python
# 建议的 researcher_loader.py 骨架（决策端开发者参照）
class ResearcherReportLoader:
    TTL_SECONDS = 2 * 3600  # 2 小时缓存
    DATA_API_URL = os.getenv("DATA_API_URL", "http://localhost:8105")

    def get_latest(self) -> Optional[Dict[str, Any]]:
        """获取最新研究员报告，TTL 内走缓存。"""
        if self._cache and (time.time() - self._loaded_at) < self.TTL_SECONDS:
            return self._cache
        return self._refresh()

    def _refresh(self) -> Optional[Dict[str, Any]]:
        url = f"{self.DATA_API_URL.rstrip('/')}/api/v1/researcher/report/latest"
        resp = httpx.get(url, timeout=5.0)
        if resp.status_code == 200:
            self._cache = resp.json()
            self._loaded_at = time.time()
            return self._cache
        return None  # 降级
```

### decision `pipeline.py` 集成位置

```python
# services/decision/src/llm/pipeline.py — prompt 构建阶段
from .researcher_loader import get_researcher_report

researcher_report = get_researcher_report()  # 可能为 None
if researcher_report:
    prompt_parts.append(f"## 研究员最新报告 ({researcher_report['segment']})\n")
    prompt_parts.append(f"期货综述: {researcher_report['futures_summary']['market_overview']}\n")
    for sym, detail in researcher_report['futures_summary']['symbols'].items():
        prompt_parts.append(f"- {sym}: {detail['trend']} (信心 {detail['confidence']})\n")
```

### decision `.env` 无需新增变量

复用现有的 `DATA_API_URL=http://192.168.31.74:8105`，路由路径不同（`/context/daily` vs `/researcher/report/latest`）。

### 数据流全景

```
              Mini (data:8105)                    Alienware (同一 data 服务)
┌──────────────────────────────┐    ┌──────────────────────────────────────┐
│  采集器 → 原始数据存储        │───→│  暂存区(staging) → qwen3:14b 归纳    │
│  preread_generator (21:00)   │    │  爬虫引擎 → 情报汇总                  │
│                              │    │            ↓                          │
│  /api/v1/context/daily  ←────│────│  /api/v1/researcher/report/latest     │
└────────────┬─────────────────┘    └──────────────┬───────────────────────┘
             │                                     │
             │  DailyContextLoader (8h TTL)        │  ResearcherReportLoader (2h TTL)
             ↓                                     ↓
       ┌─────────────────────────────────────────────────┐
       │          Studio (decision:8104)                  │
       │   pipeline.py → prompt = preread + researcher    │
       │              → LLM 推理 → 信号                    │
       └─────────────────────────────────────────────────┘
```

### 关联任务建议

TASK-0110 完成后，由 Atlas 建立 TASK-0111（或其他编号），内容：
- 新建 `services/decision/src/llm/researcher_loader.py`
- 修改 `services/decision/src/llm/pipeline.py` 注入研究员上下文
- 测试：`services/decision/tests/test_researcher_loader.py`
- 预计 1 批次 3 文件，决策端 Agent 执行
