# model_boundary 契约

状态: ACTIVE
作者: 决策 Agent
登记时间: 2026-04-07
来源冻结口径: `TASK-0021` 批次 A

## 1. 用途

本契约定义 decision 服务可对外引用的模型路线与边界约束，用于：

1. 冻结当前允许的本地与云端模型路线。
2. 为 `decision_result.md` 的 `model_profile` 提供稳定引用。
3. 明确 `XGBoost` 主线与 `LightGBM` 预留抽象位的研究边界。

## 2. 决策模型路线冻结

| profile_id | 路线角色 | model_name | deployment_class | 状态 | 说明 |
|---|---|---|---|---|---|
| `local-primary-qwen3-14b` | 本地主模型 | `Qwen3 14B` | `local` | active | 当前本地默认主模型 |
| `local-compatible-deepseek-r1-14b` | 本地兼容模型 | `DeepSeek-R1 14B` | `local` | active | 本地兼容与回退位 |
| `local-l1-qwen2.5-series` | L1 可切模型 | `Qwen2.5` | `local` | active | 轻量本地快速复核位 |
| `cloud-default-qwen3.6-plus` | 在线默认模型 | `Qwen3.6-Plus` | `cloud` | active | 云端默认复核位 |
| `cloud-review-qwen3-max` | 在线升级复核 | `Qwen3-Max` | `cloud` | active | 高等级升级复核位 |
| `cloud-fallback-deepseek-v3.2` | 在线备援模型 | `DeepSeek-V3.2` | `cloud` | active | 云端备援位 |
| `cloud-dispute-deepseek-r1` | 在线争议复核 | `DeepSeek-R1` | `cloud` | active | 争议结论复核位 |

## 3. 研究后端冻结

| backend_id | 名称 | 状态 | 说明 |
|---|---|---|---|
| `research-xgboost` | `XGBoost` | active | 当前唯一研究主线 |
| `research-lightgbm-reserved` | `LightGBM` | reserved | 仅预留抽象位，第一阶段不进入正式交付 |

## 4. 边界规则

1. 只有 `decision` 服务可以直接访问本地推理端点、云端模型 Secret、prompt 模板与内部缓存。
2. 其他服务只能通过 decision 正式 API 获取决策结果，不得绕过契约直连模型侧资源。
3. `decision_result.md` 输出的 `model_profile` 只能引用本文件已登记的 `profile_id`。
4. 研究后端与决策模型路线分层管理：`XGBoost` / `LightGBM` 属于研究层，Qwen / DeepSeek 路线属于决策审批层，不得混为一个字段体系。

## 5. model_profile 最小字段口径

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| profile_id | string | 是 | 对应第 2 节的路线 ID |
| model_name | string | 是 | 模型名称 |
| deployment_class | string | 是 | `local` / `cloud` |
| route_role | string | 是 | 本次调用中的角色描述 |

## 6. 明确排除项

以下内容不进入本契约：

- API Key、token、endpoint 地址、真实账户信息
- prompt 原文、思维链、完整对话日志
- 模型权重绝对路径、缓存路径、SQLite 行号
- legacy 模型实现细节与旧系统私有表结构