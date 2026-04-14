# REVIEW-TASK-0115 预审记录

| 字段 | 值 |
|------|-----|
| 预审ID | REVIEW-TASK-0115 |
| 任务 | TASK-0115 |
| 审核人 | Atlas（项目架构师代审） |
| 日期 | 2026-04-15 |
| 结论 | ✅ 通过 |

## 审核要点

### 1. 服务边界
- 所有修改限于 `services/decision/` 内部
- signal_validator.py / factor_monitor.py 均为新建文件
- 不修改任何已有 API 契约

### 2. 报警合规
- 使用已有 DecisionFeishuNotifier（notifier/feishu.py），不新建通知模块
- P1 报警（orange ⚠️）路径合规

### 3. 统计方法
- KS 检验与 PSI 指数为标准统计学方法，均使用 scipy 已有包
- PSI 阈值 0.25（业界标准）、KS p-value < 0.05 触发

### 4. 保护级别
- P1（新建文件，单服务范围）

### 批次白名单
- `services/decision/src/research/signal_validator.py`（新建）
- `services/decision/src/research/factor_monitor.py`（新建）
- `services/decision/tests/test_signal_validator.py`（新建）
