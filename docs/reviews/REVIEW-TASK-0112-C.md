# REVIEW-TASK-0112-C 预审记录

| 字段 | 值 |
|------|-----|
| 预审ID | REVIEW-TASK-0112-C |
| 任务 | TASK-0112 Batch C |
| 审核人 | Atlas（项目架构师代审） |
| 日期 | 2026-04-15 |
| 结论 | ✅ 通过 |

## 审核要点

### 1. 服务边界
- 所有修改限于 `services/decision/` 内部，不跨服务
- pipeline.py 已在 Batch A 白名单，Batch C 扩展不新增白名单外文件
- 不涉及 `shared/contracts/**`、P0 保护区

### 2. 自动化闭环安全性
- Optuna 调度器触发点明确：夜间21:00（与 data nightly preread 同步）
- SandboxEngine 调用在 pipeline 内部异步执行，失败后 catch 不影响主流程
- EveningRotator 补完：只修 rotate() 方法增加 K 线拉取 + _score_stock 调用，不改评分公式

### 3. Sharpe 真实化
- cross_validate 改为真实收益序列模拟交易后返回真 Sharpe
- 需要 bars 数据参数（通过 data API 拉取），接口变更向后兼容

### 4. 保护级别
- P1（非 P0 文件，单服务范围内）

### 批次白名单
- `services/decision/src/research/evening_rotation.py`
- `services/decision/src/research/optuna_search.py`
- `services/decision/src/llm/pipeline.py`
- `services/decision/tests/test_research_pipeline.py`（新建）
