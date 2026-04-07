# research_snapshot 契约

状态: ACTIVE
作者: 决策 Agent
登记时间: 2026-04-07
来源冻结口径: `TASK-0021` 批次 A

## 1. 用途

本契约定义策略研究资格快照的最小正式字段，用于：

1. 为策略仓库动作提供“研究完成”门禁证明。
2. 冻结研究主线 `XGBoost` 与 `LightGBM` 预留抽象位的外部字段边界。
3. 为后续研究中心、看板与通知链路提供统一状态引用。

## 2. 字段定义

| 字段 | 类型 | 必填 | 说明 | 约束 |
|---|---|---|---|---|
| research_snapshot_id | string | 是 | 研究快照 ID | 全局唯一 |
| strategy_id | string | 是 | 关联策略 ID | 对齐 `strategy_package.md` |
| strategy_version | string | 是 | 策略版本 | 与研究输入保持一致 |
| research_status | enum | 是 | 研究状态 | `pending` / `running` / `completed` / `failed` / `expired` |
| research_backend | enum | 是 | 研究后端 | `xgboost` / `lightgbm_reserved` |
| factor_version_hash | string | 是 | 因子版本哈希 | 用于资格门禁比对 |
| feature_set_version | string | 是 | 特征集版本 | 不暴露原始特征矩阵 |
| label_definition_version | string | 是 | 标签定义版本 | 用于复核训练口径 |
| dataset_snapshot_ref | string | 是 | 数据集快照引用 | 不写入真实路径 |
| train_window | object | 是 | 训练窗口 | 见第 3 节 |
| validation_window | object | 是 | 验证窗口 | 见第 3 节 |
| quality_gate_status | enum | 是 | 研究质量门禁 | `pass` / `manual_review` / `fail` |
| generated_at | string | 是 | 生成时间 | ISO 8601 |
| valid_until | string | 是 | 有效截止时间 | ISO 8601 |

## 3. 对象字段冻结

### 3.1 train_window

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| start_date | string | 是 | 训练开始日期，`YYYY-MM-DD` |
| end_date | string | 是 | 训练结束日期，`YYYY-MM-DD` |

### 3.2 validation_window

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| start_date | string | 是 | 验证开始日期，`YYYY-MM-DD` |
| end_date | string | 是 | 验证结束日期，`YYYY-MM-DD` |

## 4. 研究主线约束

1. `XGBoost` 是当前唯一主线研究后端，对应 `research_backend=xgboost`。
2. `LightGBM` 仅保留抽象位，对应 `research_backend=lightgbm_reserved`，第一阶段不得作为正式研究完成状态来源。
3. 研究与调参只允许运行在非交易时段；本契约只保留结果快照，不展开调度实现。
4. 若 `valid_until` 过期，`research_status` 必须视为 `expired`，相关策略失去执行资格。

## 5. 示例

```json
{
  "research_snapshot_id": "rs-20260407-0001",
  "strategy_id": "alpha-trend-001",
  "strategy_version": "2026.04.07",
  "research_status": "completed",
  "research_backend": "xgboost",
  "factor_version_hash": "fac-5511c0f3",
  "feature_set_version": "feat-v3",
  "label_definition_version": "label-v2",
  "dataset_snapshot_ref": "dataset-snapshot-20260407-alpha-trend-001",
  "train_window": {
    "start_date": "2023-01-01",
    "end_date": "2025-12-31"
  },
  "validation_window": {
    "start_date": "2026-01-01",
    "end_date": "2026-03-31"
  },
  "quality_gate_status": "pass",
  "generated_at": "2026-04-07T13:45:00+08:00",
  "valid_until": "2026-05-07T00:00:00+08:00"
}
```

## 6. 明确排除项

以下内容不进入本契约：

- 原始特征矩阵、训练样本、模型文件、参数网格
- API Key、prompt 原文、思维链、完整训练日志
- 绝对路径、缓存键、SQLite 行号
- 旧系统内部训练脚本或 legacy 研究细节