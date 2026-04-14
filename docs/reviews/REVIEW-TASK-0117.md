# REVIEW-TASK-0117 预审记录

| 字段 | 值 |
|------|-----|
| 预审ID | REVIEW-TASK-0117 |
| 任务 | TASK-0117 |
| 审核人 | Atlas（项目架构师代审） |
| 日期 | 2026-04-15 |
| 结论 | ✅ 通过 |

## 审核要点

### 1. 服务边界
- spread_monitor.py / news_scorer.py / correlation_monitor.py 均为新建文件
- daily.py / optimizer.py 已有文件，扩展部分与现有逻辑隔离（新增方法，不改旧方法）

### 2. 产业链套利触发安全
- 价差 Z-score 超阈值才触发 deepcoder → 策略生成
- 生成的策略必须走完完整 pipeline（含 phi4 审核），不直接发布
- TASK-0112-C pipeline 为前置依赖

### 3. 监控模块故障隔离
- 所有 5 个模块运行失败均捕获异常并静默，不影响主业务请求
- 失败时飞书通知（非 P0 报警，仅 P2 info 级别）

### 4. 参数退化调优安全
- Optuna 重跑结果仅为建议，差异报告推飞书后等 Jay.S 确认
- 不执行自动参数更新，不触发审批流程
- 与现有 TradeOptimizer 的内存历史兼容

### 5. 报警颜色
- 产业链套利发现：blue（资讯类 📈）
- 策略失效预警：orange（P1 ⚠️）
- 相关性漂移：yellow（P2 🔔）
- 参数退化建议：turquoise（通知类 📣）

### 6. 保护级别
- P1（3 新建 + 2 扩展，单服务范围）

### 批次白名单
- `services/decision/src/research/spread_monitor.py`（新建）
- `services/decision/src/research/news_scorer.py`（新建）
- `services/decision/src/research/correlation_monitor.py`（新建）
- `services/decision/src/reporting/daily.py`
- `services/decision/src/api/routes/optimizer.py`
- `services/decision/tests/test_research_extensions.py`（新建）
