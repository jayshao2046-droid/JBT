# TASK-0121 — data 研究员 24/7 重构（内外盘联动 + 多进程 + 连贯预读）

【创建】2026-04-16  
【服务归属】`services/data/`（子模块 `src/researcher/`）  
【执行 Agent】Claude-Code  
【状态】A0 建档完成，待签发  
【优先级】P0（决策端 phi4 依赖研究员上下文）

---

## 任务概述

对 TASK-0110 研究员子系统进行架构级重构，从"整点定时执行"改为"24/7 持续运行 + 多进程分工 + 内外盘联动追踪"，解决当前报告完全为空的问题，建立完整的 Mini → Alienware → Studio 数据链路。

---

## 问题诊断

### 当前问题（2026-04-16 诊断）

1. **报告内容完全为空**
   - 期货品种覆盖: 0 (应该 35)
   - 股票覆盖: 0 (应该 130)
   - 采集源: 0
   - 文章处理: 0
   - 报告大小: 固定 711 bytes (空模板)
   - 唯一评级: 0.0 (极度匮乏)

2. **Mini API 端点缺失**
   - Alienware 调用 `http://192.168.31.76:8105/api/v1/bars`
   - Mini data 服务**未实现此端点**
   - 导致无法读取 Mini 的 2.3 GB 采集数据

3. **架构设计不合理**
   - 整点定时执行 → 错过突发新闻
   - 一次性处理所有品种 → 效率低
   - 无内外盘联动 → 无法预判开盘走势
   - 无增量去重 → 重复读取旧数据

4. **爬虫未配置**
   - `researcher_sources.yaml` 不存在
   - 采集源注册表为空

### 数据落档现状（已确认）

**Mini 端**:
- 路径: `~/jbt/data/` (宿主机，防 Docker 重置)
- 总大小: 2.3 GB
- 期货分钟数据: `~/jbt/data/futures_minute/1m/` (353 MB, 262 品种)
- 股票分钟数据: `~/jbt/data/{股票代码}/stock_minute/records.parquet`
- Docker 挂载: 宿主机 `/Users/jaybot/jbt/data` → 容器内 `/data`
- 环境变量: `DATA_STORAGE_ROOT=/data`

**Alienware 端**:
- 硬件: i9-9900 (16 线程), 32 GB 内存, RTX 2070
- Ollama: qwen3:14b 已加载 (8.6 GB)
- 服务状态: 运行正常 (11 次执行, 0 错误)
- 网络: 万兆内网连接 Mini (低延迟)

---

## 需求来源

Jay.S 2026-04-16 确认：

### 核心需求

1. **24/7 内外盘联动追踪**
   - 内盘开盘 → 重点盯国内期货 + 相关新闻
   - 内盘休盘 → 追踪外盘（美盘、欧盘、亚太）
   - 外盘动态 → 预判内盘开盘走势

2. **基本面 + 情绪面 + 市场动态**
   - 基本面: 产业链数据、库存、仓单、产量
   - 情绪面: 新闻、社交媒体、BBS、研报
   - 市场动态: 持仓变化、资金流向、成交量

3. **爬虫采集无 API 数据**
   - 真实浏览器模式（Playwright）降低反爬风险
   - 采集网页表格、图表、PDF 报告

4. **数据链路**
   - Mini: 数据采集 + 落档存储 + API 供应
   - Alienware: 读取 Mini 数据 + 爬虫补足 + LLM 分析 + 生成报告
   - Studio: phi4 消费研报 + 评分 + 生成信号

5. **飞书和邮件**
   - 监控: Alienware 服务状态、爬虫成功率、数据质量
   - 消费: 研究员报告（实时快报 + 时段报告 + 每日深度）

---

## 新架构设计

### 数据流

```
┌─────────────────────────────────────────────────────────────┐
│  Mini (192.168.31.76) - M2 8GB                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  data 服务 (8105)                                     │  │
│  │  ├── 数据采集器 (24/7)                                │  │
│  │  │   └── 落档: ~/jbt/data/ (2.3GB)                   │  │
│  │  ├── API 端点 (新增)                                  │  │
│  │  │   ├── GET /api/v1/bars (供 Alienware 读取)        │  │
│  │  │   ├── POST /api/v1/researcher/reports (接收报告)  │  │
│  │  │   └── GET /api/v1/researcher/report/latest (供决策)│ │
│  │  └── 报告存储                                         │  │
│  │      └── ~/jbt/data/researcher/reports/              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        ↕ 万兆内网
┌─────────────────────────────────────────────────────────────┐
│  Alienware (192.168.31.224) - i9-9900 32GB RTX2070         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  研究员服务 (24/7 多进程)                             │  │
│  │                                                        │  │
│  │  进程 1: K 线监控器 (24/7)                            │  │
│  │  ├── 读取: Mini /api/v1/bars                         │  │
│  │  ├── 频率: 内盘开盘 5秒, 休盘 30秒                   │  │
│  │  ├── 品种: 35 期货主力合约                            │  │
│  │  └── 输出: 增量 K 线 → 共享队列                      │  │
│  │                                                        │  │
│  │  进程 2: 新闻爬虫 (24/7)                              │  │
│  │  ├── 模式: httpx + Playwright                        │  │
│  │  ├── 内盘开盘: 国内期货新闻 (5分钟/轮)               │  │
│  │  ├── 内盘休盘: 外盘数据 + 全球新闻 (10分钟/轮)       │  │
│  │  └── 输出: 新闻文章 → 共享队列                       │  │
│  │                                                        │  │
│  │  进程 3: 基本面爬虫 (定时)                            │  │
│  │  ├── 仓单数据 (三大交易所, 每日)                      │  │
│  │  ├── 库存数据 (港口/仓库, 每日)                       │  │
│  │  ├── 产业链数据 (上下游价格, 每小时)                  │  │
│  │  └── 输出: 基本面数据 → 共享队列                     │  │
│  │                                                        │  │
│  │  进程 4: LLM 分析器 (24/7)                            │  │
│  │  ├── 模型: qwen3:14b (Ollama 本地)                   │  │
│  │  ├── 输入: 共享队列 (K线 + 新闻 + 基本面)            │  │
│  │  ├── 分析: K线形态 + 新闻情绪 + 内外盘联动           │  │
│  │  ├── 连贯写作: 结合历史上下文，避免重复              │  │
│  │  └── 输出: 分析结果 → 报告缓冲区                     │  │
│  │                                                        │  │
│  │  进程 5: 报告生成器 (定时 + 事件触发)                 │  │
│  │  ├── 定时: 盘前/午间/盘后/夜盘收盘                    │  │
│  │  ├── 事件: 重大突发新闻/异常波动                      │  │
│  │  ├── 生成: JSON + Markdown 报告                      │  │
│  │  └── 推送: Mini API + 飞书 + 邮件                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        ↕ HTTP API
┌─────────────────────────────────────────────────────────────┐
│  Studio (192.168.31.76) - 决策端                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  decision 服务 (8104)                                 │  │
│  │  ├── ResearcherReportLoader                          │  │
│  │  │   └── 从 Mini 读取研究员报告                       │  │
│  │  ├── ResearcherReportScorer (phi4)                   │  │
│  │  │   ├── 评分: 信息完整性/逻辑一致性/时效性/可操作性  │  │
│  │  │   └── 信任度: 基于历史准确率                       │  │
│  │  └── DecisionPipeline                                │  │
│  │      └── 整合研报 + 自有分析 → 生成信号               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 报告分层

| 报告类型 | 触发方式 | 频率 | 大小 | 推送渠道 |
|---------|---------|------|------|---------|
| 实时快报 | 异常波动/重大新闻 | 事件触发 | < 1 KB | 飞书（立即）+ Mini API |
| 时段报告 | 盘前/午间/盘后/夜盘 | 4 次/天 | 10-30 KB | 飞书 + Mini API |
| 每日深度 | 每日 23:30 | 1 次/天 | 50-100 KB | 飞书 + Mini API + 邮件 |

---

## 分批计划

### 批次 M1 — Mini API 端点实现（P0，2 文件）

**目标**: 让 Alienware 能读取 Mini 的 2.3 GB 数据

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/main.py` | 修改 | 新增 `GET /api/v1/bars` 端点，读取 parquet 文件 |
| `services/data/tests/test_api_bars.py` | 新建 | 测试 bars 端点 |

**验收**:
```bash
curl "http://192.168.31.76:8105/api/v1/bars?symbol=KQ.m@SHFE.rb&start=2026-04-15T09:00:00&limit=10"
# 返回 10 条 K 线数据
```

---

### 批次 A1 — 研究员多进程骨架（P0，10 文件）

**目标**: 建立 5 进程架构 + 共享队列 + 增量去重

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/__init__.py` | 修改 | 多进程入口 |
| `services/data/src/researcher/process_manager.py` | 新建 | 进程管理器：启动/停止/监控 5 个进程 |
| `services/data/src/researcher/shared_queue.py` | 新建 | 共享队列：multiprocessing.Queue |
| `services/data/src/researcher/kline_monitor.py` | 新建 | 进程 1: K 线监控器 |
| `services/data/src/researcher/news_crawler.py` | 新建 | 进程 2: 新闻爬虫 |
| `services/data/src/researcher/fundamental_crawler.py` | 新建 | 进程 3: 基本面爬虫 |
| `services/data/src/researcher/llm_analyzer.py` | 新建 | 进程 4: LLM 分析器 |
| `services/data/src/researcher/report_generator.py` | 新建 | 进程 5: 报告生成器 |
| `services/data/src/researcher/memory_db.py` | 新建 | 增量去重 + 上下文记忆（SQLite）|
| `services/data/tests/test_researcher_multiprocess.py` | 新建 | 多进程测试 |

**验收**:
```bash
# 启动研究员服务
python -m services.data.src.researcher

# 检查 5 个进程都在运行
ps aux | grep researcher

# 检查共享队列有数据流动
# 检查 SQLite 记录增量位置
```

---

### 批次 A2 — K 线监控器实现（P0，3 文件）

**目标**: 从 Mini 增量读取 35 品种 K 线，内外盘联动

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/kline_monitor.py` | 修改 | 实现完整逻辑 |
| `services/data/src/researcher/session_detector.py` | 新建 | 时段检测：内盘开盘/休盘/外盘时段 |
| `services/data/tests/test_kline_monitor.py` | 新建 | K 线监控器测试 |

**验收**:
```bash
# 内盘开盘时段: 5 秒轮询一次
# 内盘休盘时段: 30 秒轮询一次
# 检测到异常波动 → 高优先级推送到队列
```

---

### 批次 A3 — 新闻爬虫实现（P1，6 文件）

**目标**: 双模式爬虫 + 采集源配置 + URL 去重

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/news_crawler.py` | 修改 | 实现完整逻辑 |
| `services/data/src/researcher/crawler/engine.py` | 新建 | 双模式引擎：httpx + Playwright |
| `services/data/src/researcher/crawler/parsers/generic.py` | 新建 | 通用解析器 |
| `services/data/src/researcher/crawler/parsers/futures.py` | 新建 | 期货专用解析器 |
| `services/data/configs/researcher_sources.yaml` | 新建 | 采集源配置 |
| `services/data/tests/test_news_crawler.py` | 新建 | 新闻爬虫测试 |

**验收**:
```bash
# 内盘开盘: 国内新闻源 5 分钟/轮
# 内盘休盘: 外盘新闻源 10 分钟/轮
# URL 去重生效
# Playwright 模式能绕过反爬
```

---

### 批次 A4 — 基本面爬虫实现（P1，4 文件）

**目标**: 定时采集仓单、库存、产业链数据

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/fundamental_crawler.py` | 修改 | 实现完整逻辑 |
| `services/data/src/researcher/crawler/parsers/warehouse.py` | 新建 | 仓单解析器 |
| `services/data/src/researcher/crawler/parsers/inventory.py` | 新建 | 库存解析器 |
| `services/data/tests/test_fundamental_crawler.py` | 新建 | 基本面爬虫测试 |

**验收**:
```bash
# 每日采集三大交易所仓单
# 每日采集港口库存
# 每小时采集产业链价格
```

---

### 批次 A5 — LLM 分析器 + 连贯写作（P0，4 文件）

**目标**: qwen3:14b 分析 + 结合历史上下文连贯写作

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/llm_analyzer.py` | 修改 | 实现完整逻辑 |
| `services/data/src/researcher/memory_db.py` | 修改 | 上下文记忆表 |
| `services/data/src/researcher/prompts.py` | 新建 | LLM prompt 模板 |
| `services/data/tests/test_llm_analyzer.py` | 新建 | LLM 分析器测试 |

**验收**:
```bash
# 消费队列中的 K 线/新闻/基本面数据
# 调用 qwen3:14b 分析
# 结合历史上下文，避免重复
# 输出连贯的分析结果
```

---

### 批次 A6 — 报告生成器 + 推送（P0，5 文件）

**目标**: 三层报告 + 飞书/邮件推送

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/report_generator.py` | 修改 | 实现完整逻辑 |
| `services/data/src/researcher/report_templates.py` | 新建 | 报告模板（实时/时段/每日）|
| `services/data/src/researcher/feishu_sender.py` | 新建 | 飞书推送 |
| `services/data/src/researcher/email_sender.py` | 新建 | 邮件推送 |
| `services/data/tests/test_report_generator.py` | 新建 | 报告生成器测试 |

**验收**:
```bash
# 定时生成时段报告（盘前/午间/盘后/夜盘）
# 事件触发生成实时快报
# 每日 23:30 生成深度报告
# 推送到 Mini API + 飞书 + 邮件
```

---

### 批次 D1 — Studio 决策端对接（P0，4 文件）

**目标**: phi4 消费研报 + 评分 + 生成信号

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/llm/researcher_loader.py` | 新建 | 从 Mini 读取研究员报告 |
| `services/decision/src/llm/researcher_scorer.py` | 新建 | phi4 评分机制 |
| `services/decision/src/llm/pipeline.py` | 修改 | 整合研报到决策流程 |
| `services/decision/tests/test_researcher_integration.py` | 新建 | 研报集成测试 |

**验收**:
```bash
# phi4 能读取研究员报告
# phi4 对报告进行 5 维度评分
# phi4 根据评分决定是否采纳研报
# 生成信号时整合研报 + 自有分析
```

---

### 批次 D2 — Dashboard 研究员控制台（P2，4 文件）

**目标**: 前台管理采集源 + 调整优先级 + 查看报告

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/dashboard/dashboard_web/app/data/researcher/page.tsx` | 新建 | 研究员控制台主页 |
| `services/dashboard/dashboard_web/app/data/researcher/components/source-manager.tsx` | 新建 | 采集源管理 |
| `services/dashboard/dashboard_web/app/data/researcher/components/priority-adjuster.tsx` | 新建 | 优先级调整 |
| `services/dashboard/dashboard_web/app/data/researcher/components/report-viewer.tsx` | 新建 | 报告查看 |

**验收**:
```bash
# 前台能查看所有采集源
# 前台能启用/禁用采集源
# 前台能调整品种优先级
# 前台能查看历史报告
```

---

### 批次 C1 — qwen3:14b 对话控制（P2，3 文件）

**目标**: 通过自然语言调整研究员行为

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/chat_controller.py` | 新建 | 对话控制器 |
| `services/data/src/researcher/config_updater.py` | 新建 | 配置更新器 |
| `services/data/tests/test_chat_controller.py` | 新建 | 对话控制测试 |

**验收**:
```bash
# 用户: "重点关注螺纹钢和棕榈油"
# qwen3:14b 理解并调整优先级

# 用户: "暂停采集生意社"
# qwen3:14b 禁用该采集源
```

---

## 依赖链

```
M1 (Mini API) → A1 (多进程骨架) → A2 (K线监控) → A5 (LLM分析) → A6 (报告生成) → D1 (决策对接)
                                  ↓
                                A3 (新闻爬虫) → A5
                                  ↓
                                A4 (基本面爬虫) → A5
                                  
D2 (Dashboard) 和 C1 (对话控制) 可并行，不阻塞主线
```

---

## 验收标准

### M1 验收
- Mini `/api/v1/bars` 端点返回正确的 K 线数据
- 支持 symbol, start, end, limit 参数
- 读取 parquet 文件正确

### A1-A6 验收
- 5 个进程稳定运行 24/7
- 共享队列数据流动正常
- 增量去重生效（不重复读取）
- 报告内容丰富（35 品种 + 10+ 采集源 + 50+ 文章/天）
- 报告大小: 10-50 KB (vs 当前 711 bytes)
- 飞书/邮件推送正常

### D1 验收
- phi4 能读取研究员报告
- phi4 评分机制正常
- 决策信号整合研报

### 端到端验收
- Alienware 生成报告 → 推送到 Mini → Studio phi4 消费 → 生成信号
- 内盘开盘时段: K 线 5 秒/轮，新闻 5 分钟/轮
- 内盘休盘时段: K 线 30 秒/轮，新闻 10 分钟/轮
- 异常波动 → 实时快报 → 飞书立即推送
- 每日深度报告 → 邮件推送

---

## 风险与注意事项

1. **多进程稳定性**
   - 进程崩溃自动重启
   - 共享队列满载处理
   - 内存泄漏监控

2. **爬虫反爬**
   - Playwright 模式降低风险
   - UA 轮换
   - 请求间隔随机化

3. **LLM 推理速度**
   - qwen3:14b 推理时间 ~5-10 秒/次
   - 队列积压时优先处理高优先级

4. **网络稳定性**
   - Mini API 超时重试
   - 飞书推送失败重试

5. **数据质量**
   - 爬虫成功率监控
   - 数据完整性检查
   - 异常数据告警

---

## 后续优化方向

1. **性能优化**
   - 多进程并发调优
   - qwen3:14b 推理加速（量化/批处理）

2. **数据质量**
   - 更多采集源
   - 更精准的解析器

3. **智能化**
   - 自动调整采集频率
   - 自动发现新采集源

4. **可视化**
   - Dashboard 实时监控
   - 报告质量趋势图

---

**签名**: Kiro (Claude Code)  
**日期**: 2026-04-16  
**状态**: A0 建档完成，待 Atlas 复审和 Token 签发
