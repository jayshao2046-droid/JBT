# TASK-0127 LLM 全品种自动化策略生产闭环

【类型】标准实施任务  
【建档】Atlas  
【日期】2026-04-18  
【状态】2026-04-24 decision 内部 TqSdk U0 直修已收口，待继续推进 35 品种正式执行  
【授权人】Jay.S  
【执行 Agent】Livis  
【服务边界】仅限 services/decision 单服务  
【前置】TASK-U0-20260417-006 / TASK-0124  
【工作计划】docs/handoffs/TASK-0127-LIVIS-完整工作计划-20260418.md  
【U0 开发完成时间】2026-04-18 20:50  
【Atlas 初次复核】2026-04-18 21:15（发现 5 个问题）  
【问题修复完成】2026-04-18 21:45（P1-P5 全部修复）  
【修复报告】docs/reviews/REVIEW-0127-A-Atlas-修复报告-20260418.md  
【已交付】4 个核心模块 + 1 个主控脚本 + 评分归档目录（共 1,448 行代码）

## 1. 任务目标

启动并闭环 decision 侧 LLM 自动化策略创建、调优、双回测、分级归档、证据留存流程，覆盖以下 35 个期货品种：

rb, hc, i, j, jm, cu, al, zn, ni, ss, au, ag, sc, fu, bu, ru, sp, ap, cf, sr, ma, ta, eg, pp, l, v, eb, pg, lh, p, y, a, c, cs, m

执行顺序固定为：

1. 一个品种先完成“生成 -> 调优 -> 本地回测 -> TqSdk 回测 -> 分级归档 -> 证据留存 -> 生产准入判定”。
2. 当前品种全部策略完成后，才允许进入下一个品种。
3. 35 个品种全部完成后，输出可纳入生产策略清单与阻塞清单。

## 2. 强制新增约束

### 2.1 程序异常处理

若自动化运行中出现程序问题，允许 Livis 在 Jay.S 已明确授权口径下，按 U0 规则在 decision 单服务范围内做最小应急修复，以保证 LLM 自动化流程可继续运行。

U0 仅限以下边界：

- 仅限 `services/decision/**`
- 仅限单服务最小修复
- 不得触碰 `.github/**`、`WORKFLOW.md`、`shared/contracts/**`、`shared/python-common/**`、`docker-compose.dev.yml`、`runtime/**`、`logs/**`、任何真实 `.env`
- 一旦涉及跨服务、P0/P2、目录结构扩张，立即退出 U0，回到标准预审 + Token 流程

### 2.2 分级归档目录

Livis 必须先创建过程归档目录，再执行批量生成与调优。该目录用于过程分级与证据留存，不等同于最终正式入库目录。

归档根目录冻结为：

`services/decision/strategies/llm_ranked/`

目录层级固定为：

```text
services/decision/strategies/llm_ranked/
  熔断/
    {symbol}/
  小于60分/
    {symbol}/
  60-69/
    {symbol}/
  70-79/
    {symbol}/
  80-89/
    {symbol}/
  90-100/
    {symbol}/
```

规则：

1. 所有已完成调优的策略，必须按最终评级或熔断状态迁移到对应目录。
2. 每个评分目录下，必须按品种再建子目录。
3. 原始生成目录不得删除，只允许复制或迁移后的留痕指向原始来源。
4. 最终正式可生产策略，后续若要进入正式入库库位，仍需遵守既有命名与入库铁律，不得把过程归档目录直接当作正式生产库。

### 2.3 双回测与原始证据保留

每一个完成调优的策略，必须同时通过以下两类回测，并保留原始报告：

1. 本地回测
2. TqSdk 回测

每个策略的证据目录固定为：

```text
{score_bucket}/{symbol}/{strategy_name}/
  strategy.yaml
  reports/
    generation_report.json
    optimization_report.json
    local_backtest_report.json
    tqsdk_backtest_report.json
    evaluator_report.json
```

要求：

1. `generation_report.json` 保留原始生成报告
2. `optimization_report.json` 保留调优过程摘要与最终参数
3. `local_backtest_report.json` 保留本地回测原始结果
4. `tqsdk_backtest_report.json` 保留 TqSdk 回测原始结果
5. `evaluator_report.json` 保留最终评分、等级、准入结论、阻塞原因

### 2.4 TqSdk 兼容硬约束

所有策略 YAML 必须满足手动 TqSdk 回测标准，至少包括：

1. 严格符合 JBT 当前 TqSdk YAML 模板
2. 必须包含 `transaction_costs`
3. 必须使用 ATR 止损、ATR 止盈，不得使用固定金额止损止盈字段
4. 必须包含 `risk.force_close_day: "14:55"`
5. 夜盘品种必须包含 `risk.force_close_night`
6. 必须 `no_overnight: true`
7. 使用主力合约代码，不得使用指数合约代码
8. signal 条件只允许使用模板支持字段，不得创造自定义运行时变量

## 3. 生产准入标准

### 3.1 文档级准入标准

可纳入生产的目标标准冻结为：

- Sharpe Ratio ≥ 2.5
- 最大回撤 ≤ 1.5%
- 胜率 ≥ 55%
- 盈亏比 ≥ 2.0
- 综合评分 ≥ 80 分

分级口径：

- 90-100：生产就绪，可直接进入生产候选
- 80-89：小幅调整后可上线，纳入生产候选
- 70-79：仅可进入观察池，不得直接纳入生产
- 60-69：继续优化
- 小于 60：禁止上线
- 熔断：直接终止，归入熔断目录

### 3.2 流水线硬标准

当前调优器与执行器硬标准同时必须满足：

- OOS Sharpe ≥ 1.5
- OOS 交易次数 ≥ 20
- OOS 胜率 ≥ 50%
- OOS 最大回撤 ≤ 2%
- IS/OOS Sharpe 比值 ≤ 2.0
- 年化收益目标 ≥ 15%

### 3.3 风控硬约束

延续既有策略评估强化口径：

- 单品种每日熔断 ≤ 2000 元
- 单笔止损 ≤ 1000 元
- 禁止隔夜
- 日盘 14:55 必须强平
- 月回撤不超过 2%
- 盈亏比至少达到 2:1，目标 3:1

## 4. 执行要求

### 4.1 批处理顺序

Livis 必须按品种串行，不得 35 个品种并发推进。

单品种闭环顺序固定为：

1. 建立该品种原始生成目录
2. 建立该品种分级归档目录
3. 生成策略矩阵
4. 对每个策略做调优
5. 执行本地回测
6. 执行 TqSdk 回测
7. 评分与分桶迁移
8. 保留全部报告证据
9. 输出该品种生产候选清单

### 4.2 每个品种的交付物

每个品种完成时，至少输出：

1. 该品种策略总表
2. 各策略最终等级
3. 可纳入生产候选列表
4. 熔断列表
5. 缺陷与待修复清单
6. 对应证据目录索引

### 4.3 35 品种总交付物

全部 35 个品种完成后，输出：

1. 全量生产候选策略清单
2. 全量观察池清单
3. 全量熔断清单
4. 各品种完成率
5. 尚未达标阻塞项

## 5. 建议白名单范围（待预审冻结）

本任务默认先走只读梳理，再由项目架构师按最小范围冻结白名单。候选范围预计包括：

- `services/decision/scripts/**` 与 LLM 流水线相关脚本
- `services/decision/src/research/**` 中策略生成、调优、评估、执行相关文件
- `services/decision/strategies/llm_generated/**`
- `services/decision/strategies/llm_ranked/**`
- 本任务相关 `docs/handoffs/**`

## 6. 验收标准

- [ ] 35 个品种全部进入统一流水线
- [ ] 每个品种按串行闭环完成，不跳品种
- [ ] 所有完成策略均有本地回测与 TqSdk 回测证据
- [ ] 所有策略 YAML 满足手动 TqSdk 回测要求
- [ ] 所有策略进入固定评分目录分桶
- [ ] 所有可生产策略都有明确准入证据
- [ ] 所有熔断策略都有熔断留痕与原因

## 7. U0 开发完成情况（2026-04-18 20:50）

### 7.1 已交付文件

#### 核心模块（4 个）
- `services/decision/src/research/tqsdk_backtest_client.py` (284 行)
  - TqSdk 回测客户端，通过 Studio backtest API 提交回测任务
  - 轮询获取回测结果，YAML 预处理与验证
  
- `services/decision/src/research/evidence_manager.py` (323 行)
  - 证据管理器，管理 5 份报告的生成与存储
  - 策略评分分桶迁移，证据文件归档
  
- `services/decision/src/research/feishu_strategy_notifier.py` (227 行)
  - 飞书通知器，富文本卡片格式
  - 包含双回测对比结果、所有参数、落盘位置
  
- `services/decision/src/research/contract_resolver.py` (200 行)
  - 合约解析器，主力合约月份解析
  - DCE.p0 → DCE.p2505 转换，降级方案

#### 主控脚本（1 个）
- `services/decision/scripts/run_full_pipeline_35_symbols.py` (414 行)
  - 35 品种串行执行主控脚本
  - 完整闭环流程：生成→调优→双回测→评分→归档→通知
  - 断点续传机制，进度追踪

#### 目录结构
- `services/decision/strategies/llm_ranked/` (217 个目录)
  - 6 个评分目录 × 35 个品种子目录
  - README.md 说明文档

### 7.2 代码统计
- 总代码行数：1,448 行
- 核心模块：1,034 行
- 主控脚本：414 行

### 7.3 核心特性
- ✅ 完全自动化闭环（生成→调优→双回测→评分→归档→通知）
- ✅ 飞书实时通知（每个策略完成后立即发送）
- ✅ 双回测验证（本地 + TqSdk，≥ 2 年）
- ✅ 完整证据留存（5 份报告）
- ✅ 断点续传机制

### 7.4 下一步行动
1. 集成测试（单策略 + 单品种）
2. 正式执行 35 品种流水线

### 7.5 2026-04-24 U0 直修补丁（decision 单服务）

#### 背景

- 单品种真实探针已确认 TqSdk 提交链路能到达 decision 内部 formal runner。
- 现场症状表现为 `poll_result()` 长等待超时，但 Air 的 backtest 服务同类回测可以正常完成。
- 最终确认这不是单纯超时窗口过短，而是 decision 侧复用了 Air 运行态从未走过的异步调度分支。

#### 根因

1. Air `services/backtest/src/api/routes/backtest.py` 的正式回测路径是后台线程直接调用 `runner.run_job_sync(job_input)`。
2. decision `services/decision/src/research/tqsdk_backtest_client.py` 走的是 `runner.submit()` → `asyncio.create_task()` → `wait_for_job()` 的异步调度链路。
3. 两边 `runner.py` / `session.py` 实现虽然一致，但 Air 生产实际只验证过“线程 + 同步直跑”路径，没有验证 `submit/_execute/_semaphore/wait_for_job` 这条路径。
4. 因此 decision 内部出现了“任务已提交，但 TqSdk 长时间不回收结果”的假超时现象。

#### 修复

- 修复文件：`services/decision/src/research/tqsdk_backtest_client.py`
- 修复方式：
  1. `submit_backtest()` 不再调用 `OnlineBacktestRunner.submit()`，仅登记规范化后的 `BacktestJobInput`
  2. `poll_result()` 改为 `asyncio.to_thread(self._runner.run_job_sync, job_input)` 同步直跑
  3. 执行模型与 Air 的 `_run_backtest_background -> runner.run_job_sync()` 保持一致

#### 验证

- 探针策略：`rb_trend_60m_v1`
- 验证区间：`2024-01-01 ~ 2024-06-30`
- 结果：修复后 `29.9s` 内返回 `status=completed`
- 结论：decision 内部 TqSdk 正式回测结果回收链已恢复；原“超时”症状根因已排除

## 8. 当前派发结论

U0 开发阶段已完成，且 2026-04-24 decision 内部 TqSdk 结果回收链已完成事后修复收口。当前阻塞已从“TqSdk 长等待超时”收敛为其余候选策略自身的 YAML / 数据 /调优问题，可继续推进后续 35 品种正式执行与剩余问题剥离。