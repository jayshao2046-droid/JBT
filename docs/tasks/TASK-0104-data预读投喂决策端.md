# TASK-0104 — data 预读投喂决策端（夜间摘要生成 + 开盘前上下文注入）

| 字段 | 值 |
|------|------|
| **任务ID** | TASK-0104 |
| **服务** | data → decision |
| **优先级** | P2 |
| **类型** | feat |
| **状态** | ✅ 全部完成（D1 commit 802c1f7 / D2 commit d356511 / 2026-04-15） |
| **创建时间** | 2026-04-14 |
| **依赖** | master plan 5.7 节；依赖 Ollama 三模型已部署（✅ TASK-0083 已完成）；依赖 watchlist CB5（✅ TASK-0054 已完成）；依赖 C0-1 股票 bars 路由（✅ TASK-0050 已完成） |
| **关联** | TASK-0081, TASK-0083（LLM Pipeline 已落地） |

---

## 背景

master plan 5.7 节定义的"数据端预读投喂决策端"目前**未落地**。

现有情况：
- `phi4-reasoning` 的 `/api/v1/llm/analyze` 支持按需传入 `symbol+timeframe` 实时拉 K 线（已在 TASK-0083 实现）
- 但这是**按需实时拉取**，每次调用都触发 data 服务请求，无缓存，无预聚合
- 盘中实时决策链路依赖网络与 data 服务可用性，引入不确定延迟

目标：
- 非交易时段（前夜 21:00 ~ 次日 08:30）由 data 服务预读并聚合数据
- 生成结构化摘要文件（JSON/Parquet），存入共享目录或 data API 缓存层
- decision 开盘前（08:30）拉取预读摘要，注入 LLM 上下文，缩短盘中决策链路延迟

---

## 数据资产分析

### 当前 data 服务 Collector 全表

| Collector | 数据类型 | 数据源 | 覆盖品种 |
|-----------|----------|--------|---------|
| `TushareDailyCollector` | 股票日线 OHLCV | Tushare | 全 A 股 |
| `TushareFullCollector` | 日线+基本面（PE/PB/市值）| Tushare | 全 A 股 |
| `TushareFuturesCollector` | 期货日线 | Tushare | 主力合约 |
| `StockMinuteCollector` | 股票分钟 K 线 | Tushare | watchlist 范围 |
| `OverseasMinuteCollector` | 海外期货分钟 K | AkShare | 外盘期货 |
| `TqSdkCollector` | 期货分钟 K（实时）| 天勤 TqSdk | 国内期货 |
| `NewsAPICollector` | 财经新闻 | 东财/CLS/新浪/上期所/证券时报 | 全市场 |
| `RSSCollector` | RSS 新闻 | 财联社/路透/Bloomberg RSS | 全市场 |
| `MacroCollector` | 宏观指标 CPI/PPI/PMI/GDP | AkShare | CN/US/EU/JP/UK/AU/CA |
| `SentimentCollector` | 融资融券/北向资金/市场活跃度 | AkShare | 上交所/深交所 |
| `CftcCollector` | CFTC 净持仓报告 | AkShare | 黄金/白银/铜/原油/天然气/玉米/大豆/小麦/SP500/NASDAQ |
| `OptionsCollector` | 期权链（隐含波动率）| AkShare | 50ETF/300ETF 期权 |
| `ForexCollector` | 汇率 | AkShare | USD/CNY/EUR/GBP/JPY 等 |
| `ShippingCollector` | 航运指数 BDI | AkShare | 波罗的海干散货 |
| `VolatilityCollector` | 波动率指数 | AkShare | 50ETF QVIX / 300ETF QVIX / CBOE VIX / VXN |

---

## 数据 → 决策模型投喂映射分析

### 决策端模型角色定义（TASK-0083 已部署）

| 角色 | 模型 | env key | LLM Pipeline 中的职责 |
|------|------|---------|----------------------|
| 研究员 | `deepcoder:14b` | `OLLAMA_RESEARCHER_MODEL` | 将策略意图转译为 YAML + Python 代码 |
| 审核员（主模型 L2）| `qwen3:14b` | `OLLAMA_AUDITOR_MODEL` / `LOCAL_MODEL_MAIN` | 完整性/风控/因子可用性校验，输出 pass/fail+issues |
| L1 快速审查 | `Qwen2.5` | `LOCAL_MODEL_L1` | 第一道门控，快速过滤显而易见的问题 |
| 数据分析师 | `phi4-reasoning:14b` | `OLLAMA_ANALYST_MODEL` | 量化绩效归因、K 线分析、风险评估与调优建议 |
| 兼容/容灾备援 | `DeepSeek-R1-14b` | `LOCAL_MODEL_COMPAT` | 主模型不可用时接替 |

---

### 各角色所需上下文与对应 Collector

#### 研究员（deepcoder:14b）— 策略意图 → 代码生成

研究员的核心输入是**用户口头策略意图**，但需要上下文约束生成结果的可执行性和合理性。

| 数据类型 | Collector | 用途 | 投喂方式 |
|----------|-----------|------|---------|
| watchlist 股票池 | `StockMinuteCollector` / watchlist_client | 约束标的范围，避免生成无法执行的标的选择 | 注入 system prompt：`当前可交易标的池：{watchlist}` |
| 近 5 日日线摘要（标的平均涨跌/成交量） | `TushareDailyCollector` | 提供近期价格区间参考，避免参数严重偏离市场实际 | prompt 附加：`近5日市场概况：{summary}` |
| 宏观背景快照（最新 CPI/PPI/PMI 月度值） | `MacroCollector` | 区分牛熊/通胀环境，影响策略方向选择（趋势 vs 均值回归） | prompt 附加：`当前宏观环境：{macro_summary}` |
| CFTC 大宗商品净持仓方向 | `CftcCollector` | 期货策略研究员需了解当前多空格局 | prompt 附加（期货策略专用）：`主要品种持仓方向：{cftc_snapshot}` |

**预期提升**：研究员生成的策略与当前市场环境更匹配，减少 L2 审核打回率（当前无上下文时策略参数经常偏离市场实际）。

---

#### L1 快速审查（Qwen2.5）— 第一道门控

L1 做快速响应，不做深度分析，需要**轻量但关键**的市场状态信号。

| 数据类型 | Collector | 用途 | 投喂方式 |
|----------|-----------|------|---------|
| 市场情绪简报（北向资金今日净买卖、融资融券余额变化） | `SentimentCollector` | 判断当前市场多空偏向，过滤逆势策略意图 | prompt 附加：`今日市场情绪: 北向{x}亿, 融资余额{y}` |
| 重大新闻标题列表（近 12h Top 10） | `NewsAPICollector` + `RSSCollector` | 检测重大事件（政策/突发），触发风控阻断 | prompt 附加：`近12h重要新闻摘要：{titles}` |
| 波动率指数（50ETF QVIX / VIX）| `VolatilityCollector` | 高波动期自动提高风控门槛 | prompt 附加：`当前波动率: QVIX={val}, VIX={val}` |

**预期提升**：L1 能捕获"当前发布重大政策/黑天鹅"场景，提前阻断不合时宜的策略研究请求，不消耗昂贵的 L2/研究员算力。

---

#### 审核员（qwen3:14b / 主模型 L2）— 深度策略合理性审核

L2 做完整审核，需要**较完整的量化背景信息**来评判策略参数合理性。

| 数据类型 | Collector | 用途 | 投喂方式 |
|----------|-----------|------|---------|
| 近 20 日分钟 K 线统计（均值/标准差/最大振幅）| `StockMinuteCollector` | 校验策略信号频率合理性（如 MA 周期与实际波动率匹配度）| prompt 附加：`{symbol} 近20日分钟K统计：振幅avg={x}% std={y}%` |
| 历史波动率（20日/60日 ATR）| `TushareDailyCollector` 派生 | 校验 max_drawdown 参数是否与标的真实波动率匹配 | prompt 附加：`{symbol} 20日ATR={x}, 60日ATR={y}` |
| 期权隐含波动率（IV 与 HV 差值 IV skew）| `OptionsCollector` | 判断市场对未来波动的定价（适用股票策略的波动率参数校准）| prompt 附加：`当前 IV vs HV 差值：{iv_skew}` |
| 宏观月报（完整 CPI/PPI/PMI 序列）| `MacroCollector` | 在宏观转折点识别策略是否与当前周期匹配 | prompt 附加：`宏观指标近3月序列：{macro_series}` |
| 汇率（USD/CNY）近期变化幅度 | `ForexCollector` | 外资敏感型策略的汇率风险校核 | prompt 附加（可选）：`近30日USD/CNY变化：{delta}%` |

**预期提升**：消除目前因"策略 ATR 止损参数设 0.5% 但标的日振幅普遍 3%"导致的虚假通过问题。

---

#### 数据分析师（phi4-reasoning:14b）— 绩效归因与量化分析

数据分析师负责事后/研究期间的深度量化分析，需要**最完整**的数据上下文。

| 数据类型 | Collector | 用途 | 投喂方式 |
|----------|-----------|------|---------|
| 完整 K 线 OHLCV（日线 250 根 + 分钟 K 线样本）| `TushareFullCollector` + `StockMinuteCollector` | 收益归因的基础原始数据 | 直接结构化注入（已有 TASK-0083 实现，按需拉取） |
| 波动率指数序列 | `VolatilityCollector` | 评估策略在不同波动率区间的表现差异 | 附加时序数据：`VIX序列近30日：[...]` |
| CFTC 净持仓变化趋势（近 8 周）| `CftcCollector` | 大宗商品期货策略的机构行为分析 | 附加：`黄金/原油持仓净多净空趋势：{series}` |
| 北向资金近 20 日净买入排名 | `SentimentCollector` | 外资流向与策略标的重合度分析 | 附加：`北向净买入 Top10：{list}` |
| BDI 航运指数 | `ShippingCollector` | 上游大宗商品需求的领先指标（周期策略参考） | 附加（可选）：`BDI近30日：{series}` |
| 融资融券余额变化率 | `SentimentCollector` | A 股杠杆资金的聪明钱信号 | 附加：`融资余额近20日变化率：{delta}` |

---

## 实施方案

### 核心架构：夜间摘要生成器（data 侧）

```
data 服务新增调度任务（Scheduler）
├── 21:00  启动夜间预读任务
│   ├── 拉取全量日线 + watchlist 分钟 K（今日收盘数据）
│   ├── 拉取新闻（近 12h）
│   ├── 拉取宏观快照（最新月度值）
│   ├── 拉取情绪数据（融资融券/北向）
│   └── 拉取 CFTC + 波动率（每周/每日更新）
├── 22:00  生成分角色摘要文件
│   ├── researcher_context.json  -- 研究员上下文
│   ├── l1_briefing.json         -- L1 快速简报
│   ├── l2_audit_context.json    -- L2 审核上下文
│   └── analyst_dataset.json     -- 数据分析师完整数据集
└── 23:00  验证文件完整性，写入 ready_flag，推送飞书通知
```

### 调用层（decision 侧）

```
decision 服务在以下时机读取预读文件：
├── 服务启动（08:30 前后）→ 缓存到内存
├── /api/v1/llm/research 调用时 → 注入 researcher_context
├── /api/v1/llm/audit 调用时 → 注入 l2_audit_context / l1_briefing
└── /api/v1/llm/analyze 调用时 → 优先用 analyst_dataset 补充 K线，减少实时拉取
```

### 文件位置（待定，需 Architect 预审确认）

```
data 服务生产路径（初步方案）：
  services/data/runtime/daily_snapshots/{YYYY-MM-DD}/
    ├── researcher_context.json
    ├── l1_briefing.json  
    ├── l2_audit_context.json
    ├── analyst_dataset.json
    └── ready_flag.txt   # 写入时间戳，decision 侧校验新鲜度
```

> ⚠️ `runtime/` 路径属于永久禁改区，不进 Git；文件由 data 服务运行时生成，decision 侧只读访问。

---

## 待拆分子任务

| 子任务 | 归属服务 | 初步估计文件范围 |
|--------|----------|----------------|
| D0: 摘要数据结构设计（JSON schema）| 架构师预审 | shared/contracts（若需跨服务契约） |
| D1: data 侧夜间调度任务 + 摘要生成器 | data | ~5 文件 |
| D2: decision 侧 context_loader（读取预读文件注入 prompt）| decision | ~3 文件 |
| D3: LLM pipeline 分角色 prompt 模板增强 | decision | `llm/prompts.py`（已有，修改） |
| D4: 飞书通知（预读完成/失败告警）| data | ~1 文件 |
| D5: 健康检查（预读文件新鲜度校验）| decision | ~1 文件 |

---

## 预审前置问题（需 Architect 确认）

1. **文件共享方式**：runtime 目录直接共挂（同机）？还是通过 data API 的新接口暴露（`GET /api/v1/context/daily`）？推荐后者，保持服务边界。
2. **触发时机**：decision 是服务启动时拉取一次还是每次 LLM  调用时懒加载？推荐启动缓存 + TTL 刷新。
3. **data API 新接口是否需要走 contracts 契约**：若 decision 通过 HTTP 拉取预读数据，需在 `shared/contracts` 登记 `DailyContext` 响应模型。
4. **watchlist 标的范围**：预读 K 线时只覆盖当前 watchlist，还是全量 A 股（数据量差距 10x）？

---

## 当前状态

- [x] 需求确认（5.7 节规划，2026-04-14 Jay.S 明确要做）
- [x] 数据资产盘点与投喂映射分析（本文档）
- [x] 架构师预审（Atlas 快裁代行，REVIEW-TASK-0104-PRE，2026-04-15）
- [x] shared/contracts 契约（不适用，data 单向暴露聚合端点，无需跨服务契约）
- [x] Token 签发（D1: tok-97335b68 / D2: tok-54f501ef，2026-04-15）
- [x] D1 data 侧：完成（commit 802c1f7，6/6 passed，2026-04-15）
- [x] D1 验收与 lockback（tok-d8f23d88 locked，Atlas 复核通过）
- [x] D2 decision 侧：完成（commit d356511，6/6 passed，2026-04-15）
- [x] D2 验收与 lockback（tok-6f298133 locked，Atlas 复核通过）
- [x] 两地同步（git push + Mini/Studio 同步，2026-04-15）
