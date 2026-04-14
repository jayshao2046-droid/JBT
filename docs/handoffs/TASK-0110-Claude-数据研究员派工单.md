# TASK-0110 Claude 派工单 — 数据研究员子系统

【创建】2026-04-15
【任务文件】`docs/tasks/TASK-0110-data-researcher-数据研究员子系统.md`
【预审文件】`docs/reviews/TASK-0110-review.md`
【锁控文件】`docs/locks/TASK-0110-lock.md`
【执行 Agent】Claude-Code
【执行策略】A → B → C → D → E 一次性全批执行，全部完成后统一核验。不必等单批验证再进入下批，但代码依赖顺序仍为 A→B→C→D→E。

---

## 项目背景

在 data 服务内新增"数据研究员"子系统：
- **设备**：Alienware（192.168.31.224），RTX 2070 8GB，qwen3:14b via Ollama (http://192.168.31.224:11434)
- **数据源**：Mini（192.168.31.76:8105）全量采集数据 + 双模式爬虫
- **产出**：四段制双格式报告（JSON 决策版 + Markdown Jay 版）
- **消费者**：决策端（Studio 192.168.31.142:8104）通过 `/api/v1/researcher/report/latest` 读取

## 关键技术约定

### Alienware Ollama 调用
```python
import httpx
OLLAMA_URL = "http://192.168.31.224:11434"
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

## 后续关联任务提示

TASK-0110 完成后，需建立 TASK-0111（决策端对接）：
- 新建 `services/decision/src/llm/researcher_loader.py`
- 修改 `services/decision/src/llm/pipeline.py`
- 新建 `services/decision/tests/test_researcher_loader.py`
- 详见任务文件"决策端对接指南"章节
