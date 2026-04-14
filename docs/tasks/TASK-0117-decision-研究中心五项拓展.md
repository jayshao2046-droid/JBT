# TASK-0117 — 决策端研究中心 5 项拓展

【创建】2026-04-15
【服务归属】`services/decision/`
【执行 Agent】Claude-Code
【复核】Atlas
【状态】建档完成，待签发

## 任务概述

扩展研究中心能力至 5 个新方向：产业链价差套利自动发现、策略失效预警、盘前资讯过滤打分、参数退化自动再调优、跨品种相关性漂移监控。所有功能均无人值守自动运行，异常时飞书报警。

## 5 个拓展模块

### 模块 1：产业链价差监控

监控期货产业链内的价差 Z-score：
- 黑色链：rb-hc-i-j-jm
- 有色链：cu-al-zn
- 油脂链：p-y-a

Z-score > 2σ → deepcoder 自动生成套利策略意图 → 走完研究流水线 → 输出可用套利策略

### 模块 2：策略失效预警

每日收盘后对已上线策略做 30 日滚动 Sharpe 评估：
- Sharpe 下滑 > 30% 且连续 5 日 → 飞书 P1 报警 + 触发重新调优
- 不自动更新参数，需 Jay.S 确认后走审批流程

### 模块 3：盘前资讯过滤打分

qwen3 研报生成后，deepcoder 对每条资讯打标：
- "影响品种"标签（哪些品种可能受影响）
- 紧急程度评分（0-10）
- 已持有品种相关资讯若评分 > 7 → 飞书推送

### 模块 4：参数退化自动再调优

每周一夜间自动为每个已上线策略跑一次 Optuna：
- 新最优参数与当前参数差异 < 5% → 维持
- 差异 > 15% → 飞书通知 Jay.S 是否更新参数
- 不自动部署，需人工确认

### 模块 5：跨品种相关性漂移

每日计算 35 品种相关矩阵与历史均值偏差：
- 某对品种相关性偏离历史 > 2σ → 飞书通知（P2 告警）
- 识别短暂套利窗口 + 标记可能的基本面变化信号

## 分批计划

### Batch A — 5 模块核心（P1，6 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/research/spread_monitor.py` | 新建 | 产业链价差监控：拉取跨品种日K线 → Z-score → 触发阈值时自动构造意图调 pipeline |
| `services/decision/src/research/news_scorer.py` | 新建 | 盘前资讯打分：读研报 → 调 deepcoder 打标 → 高分资讯飞书推送 |
| `services/decision/src/research/correlation_monitor.py` | 新建 | 跨品种相关性漂移：35品种相关矩阵 → 偏离检测 → 飞书P2报警 |
| `services/decision/src/reporting/daily.py` | 修改 | 新增策略失效预警：30日滚动Sharpe 对比 + P1报警触发 |
| `services/decision/src/api/routes/optimizer.py` | 修改 | 新增参数退化再调优：每周自动重跑Optuna，差异报告飞书推送 |
| `services/decision/tests/test_research_extensions.py` | 新建 | 测试5个模块：mock数据验证触发/不触发/报警路径 |

## 质量标准

- 所有监控模块运行失败不影响主业务流程（异常捕获静默）
- 飞书报警遵循统一颜色标准（产业链套利 blue 资讯类，策略失效 orange P1，相关性漂移 yellow P2）
- 参数退化调优以不覆盖生产为原则，只建议不自动部署
- 相关矩阵计算窗口：60 个交易日历史 vs. 近 5 日

## 依赖

- 读取 data API 获取跨品种K线
- 读取 researcher/report/latest 获取qwen3研报
- 调用 pipeline.full_pipeline() 构造套利策略（依赖 TASK-0112-C 完成）
- optimizer.py 已有基础实现，本任务在其上扩展
