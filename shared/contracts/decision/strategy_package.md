# strategy_package 契约

状态: ACTIVE
作者: 决策 Agent
登记时间: 2026-04-07
来源冻结口径: `TASK-0021` 批次 A

## 1. 用途

本契约定义 decision 服务中策略仓库的最小正式元数据模型，用于：

1. 冻结策略包导入、导出、预约、执行、下架的稳定字段边界。
2. 关联研究快照、回测证明与因子版本，形成执行资格门禁。
3. 为后续看板、发布编排与通知链路提供统一索引。

## 2. 字段定义

| 字段 | 类型 | 必填 | 说明 | 约束 |
|---|---|---|---|---|
| strategy_id | string | 是 | 策略唯一标识 | 全局稳定 ID |
| strategy_name | string | 是 | 策略名称 | 面向审阅与展示 |
| strategy_version | string | 是 | 当前策略版本 | 不绑定内部路径 |
| template_id | string | 是 | 模板标识 | 指向策略模板类别 |
| package_hash | string | 是 | 当前策略包快照哈希 | 用于导入/导出一致性校验 |
| factor_version_hash | string | 是 | 因子版本哈希 | 与研究快照、回测证明对齐 |
| factor_sync_status | enum | 是 | 因子同步状态 | `aligned` / `mismatch` / `unknown` |
| research_snapshot_id | string | 是 | 关联研究快照 ID | FK → `research_snapshot.md` |
| backtest_certificate_id | string | 是 | 关联回测证明 ID | FK → `backtest_certificate.md` |
| risk_profile_hash | string | 是 | 风控快照哈希 | 用于执行资格对齐 |
| config_snapshot_ref | string | 是 | 配置快照引用 | 可为对象存储键或逻辑引用 |
| lifecycle_status | enum | 是 | 生命周期状态 | 见第 3 节 |
| allowed_targets | string[] | 是 | 允许发布目标 | 第一阶段固定仅 `sim-trading` |
| publish_target | string | 否 | 当前预约或发布目标 | 第一阶段仅 `sim-trading` |
| live_visibility_mode | enum | 是 | 实盘可见模式 | 固定为 `locked_visible` |
| reserved_at | string | 否 | 预约时间 | ISO 8601 |
| published_at | string | 否 | 进入发布流程时间 | ISO 8601 |
| retired_at | string | 否 | 下架时间 | ISO 8601 |
| created_at | string | 是 | 创建时间 | ISO 8601 |
| updated_at | string | 是 | 最近更新时间 | ISO 8601 |

## 3. 生命周期冻结

| 状态 | 含义 |
|---|---|
| imported | 已导入策略仓库，尚未预约发布 |
| reserved | 已预约发布窗口 |
| publish_pending | 已进入发布流程，等待下游消费 |
| published | 已被目标服务确认接收 |
| retired | 已下架，不再允许新发布 |

补充说明：

1. “导出”是只读动作，不单独新增生命周期状态。
2. “执行”只把状态推进到 `publish_pending` 或 `published`，不代表直接下单。
3. `live_visibility_mode` 第一阶段固定为 `locked_visible`，不允许出现 `live-trading` 可执行状态。

## 4. 动作与状态变更关系

| 动作 | 输入要求 | 输出要求 |
|---|---|---|
| 导入 | 策略包快照 + 研究快照 + 回测证明均有效 | `lifecycle_status=imported` |
| 导出 | `strategy_id` 存在 | 返回当前快照，不改变生命周期 |
| 预约 | 策略包未下架，且资格门禁通过 | `lifecycle_status=reserved`，写入 `reserved_at` |
| 执行 | 目标仅 `sim-trading`，且资格门禁通过 | 进入 `publish_pending` 或 `published` |
| 下架 | 策略包存在 | `lifecycle_status=retired`，写入 `retired_at` |

## 5. 资格门禁约束

1. `factor_version_hash` 必须同时与 `research_snapshot.md` 和 `backtest_certificate.md` 对齐。
2. 研究快照失效、回测证明过期、风控哈希漂移时，策略包不得进入预约或执行。
3. 第一阶段 `allowed_targets` 只允许 `sim-trading`；`live-trading` 只允许保留锁定可见状态，不得进入 `allowed_targets`。

## 6. 响应示例

```json
{
  "strategy_id": "alpha-trend-001",
  "strategy_name": "Alpha Trend Futures",
  "strategy_version": "2026.04.07",
  "template_id": "trend-template-v1",
  "package_hash": "pkg-8d98f7b2",
  "factor_version_hash": "fac-5511c0f3",
  "factor_sync_status": "aligned",
  "research_snapshot_id": "rs-20260407-0001",
  "backtest_certificate_id": "bc-20260407-0001",
  "risk_profile_hash": "risk-442d0a91",
  "config_snapshot_ref": "strategy-config-alpha-trend-001-20260407",
  "lifecycle_status": "reserved",
  "allowed_targets": ["sim-trading"],
  "publish_target": "sim-trading",
  "live_visibility_mode": "locked_visible",
  "reserved_at": "2026-04-07T14:30:00+08:00",
  "published_at": null,
  "retired_at": null,
  "created_at": "2026-04-07T14:00:00+08:00",
  "updated_at": "2026-04-07T14:30:00+08:00"
}
```

## 7. 明确排除项

以下内容不进入本契约：

- 策略源码全文、prompt 模板原文、思维链文本
- 原始研究数据集、回测逐笔成交列表、原始报告文件内容
- 绝对路径、临时目录、SQLite 行号
- legacy 策略仓库内部字段与旧系统私有状态