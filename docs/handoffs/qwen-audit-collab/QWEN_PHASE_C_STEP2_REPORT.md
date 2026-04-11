# Qwen Phase C Step 2 Report

【签名】Roo
【时间】2026-04-11
【设备】MacBook

## 1. Step 2 执行摘要

基于 Step 1 的全量拆批矩阵，对首批三项候选项（C0-1、CB5、CG2）进行了详细分析。确认了这些项目的当前状态、真实仓库锚点、依赖关系和准备情况。所有分析均基于只读检查，未修改任何文件。

## 2. 候选项 A：C0-1

### 基本信息
- 候选项编号与名称：C0-1 股票 bars API 路由扩展
- 当前是否具备进入预审条件：`ready-for-pre-review`
- 主责服务：数据
- 协同服务：决策

### 技术详情
- 真实仓库锚点：`services/data/src/main.py`（现有anchor）
- 建议最小业务文件范围（只是建议，不是白名单）：
  - `services/data/src/main.py`
  - `services/data/src/api/routes/stock_bars.py`（待创建）
  - `services/data/src/data/storage.py`（可能需要扩展）
- 依赖项：无
- 最小验证方式：API 测试，验证股票代码解析与 `stock_daily/stock_minute` 供数功能
- 主要风险：无显著风险
- 是否触及受保护区域：否
- 锚点类型：`existing-anchor`
- Atlas 若要建单，最适合拆成几批：1 批

## 3. 候选项 B：CB5

### 基本信息
- 候选项编号与名称：CB5 动态 watchlist 分钟 K 采集
- 当前是否具备进入预审条件：`ready-for-pre-review`
- 主责服务：数据
- 协同服务：决策

### 技术详情
- 真实仓库锚点：`services/data/src/collectors/stock_minute_collector.py`（现有anchor）
- 建议最小业务文件范围（只是建议，不是白名单）：
  - `services/data/src/collectors/stock_minute_collector.py`
  - `services/data/src/scheduler/pipeline.py`（可能需要修改调度逻辑）
  - `services/data/src/utils/config.py`（可能需要配置watchlist）
- 依赖项：C0-1（股票 bars API 路由扩展）
- 最小验证方式：运行采集器，验证是否按 watchlist 动态采集而非全量轮询
- 主要风险：可能增加数据采集负载
- 是否触及受保护区域：否
- 锚点类型：`existing-anchor`
- Atlas 若要建单，最适合拆成几批：1 批

## 4. 候选项 C：CG2

### 基本信息
- 候选项编号与名称：CG2 人工手动回测 + 审核确认
- 当前是否具备进入预审条件：`ready-for-pre-review`
- 主责服务：回测
- 协同服务：决策

### 技术详情
- 真实仓库锚点：`services/backtest/src/backtest/runner.py` + `services/backtest/src/api/routes/strategy.py`（现有anchor）
- 建议最小业务文件范围（只是建议，不是白名单）：
  - `services/backtest/src/backtest/runner.py`
  - `services/backtest/src/api/routes/strategy.py`
  - `services/backtest/src/backtest/session.py`
  - `services/backtest/src/backtest/manual_runner.py`（待创建）
  - `services/backtest/src/api/routes/approval.py`（待创建）
- 依赖项：CG1（回测端策略导入队列）
- 最小验证方式：手动触发回测，验证审核确认流程
- 主要风险：无显著风险
- 是否触及受保护区域：否
- 锚点类型：`existing-anchor`
- Atlas 若要建单，最适合拆成几批：1 批

## 5. 三项并行 / 串行关系

- C0-1 和 CB5 存在串行依赖：CB5 依赖 C0-1 完成
- CG2 独立于 C0-1 和 CB5，可并行推进
- 建议执行顺序：C0-1 → CB5，同时 CG2 可独立启动

## 6. 给 Atlas 的预审建议顺序

1. 优先处理 C0-1（股票 bars API 路由扩展），这是 CB5 的前置依赖
2. 同时可启动 CG2（人工手动回测 + 审核确认），因其独立于数据端改造
3. CB5（动态 watchlist 分钟 K 采集）在 C0-1 完成后立即启动

## 7. 给 Jay.S 的一句话摘要

首批三项 Phase C 任务（C0-1 股票 API 扩展、CB5 动态采集、CG2 人工回测）均已具备预审条件，建议按 C0-1→CB5 串行、CG2 并行的方式推进。