# Bridge Signal Contract — sim-trading

**版本：** v1.0
**任务：** TASK-0012
**保护级别：** P0
**文档作者：** 项目架构师
**建档时间：** 2026-04-06

---

## 说明

本文件定义 legacy J_BotQuant Studio → JBT SimNow 桥接信号的最小字段模型。  
所有字段均为必填（price 在市价场景可为 null）。

---

## 字段清单

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| signal_id | string (UUID) | ✅ | 信号唯一 ID，用于幂等与去重 |
| source_system | string | ✅ | 来源系统标识，固定为 `legacy-jbotquant` |
| source_instance_id | string | ✅ | 来源实例或节点标识，用于审计与冲突排查 |
| strategy_id | string | ✅ | 策略标识 |
| strategy_version | string | ✅ | 策略版本号 |
| trace_id | string (UUID) | ✅ | 跨链路追踪 ID |
| generated_at | string (ISO 8601) | ✅ | 信号生成时间 |
| expires_at | string (ISO 8601) | ✅ | 信号过期时间，TTL 校验唯一口径 |
| sequence_no | integer | ✅ | 来源侧单调序号，用于乱序判断 |
| account_id | string | ✅ | 目标账户标识 |
| symbol | string | ✅ | 目标合约代码（如 CZCE.CF605） |
| side | string | ✅ | 买卖方向：`buy` 或 `sell` |
| offset | string | ✅ | 开平标志：`open`、`close`、`close_today` |
| volume | integer | ✅ | 下单数量（手数） |
| order_type | string | ✅ | 订单类型：`limit` 或 `market` |
| price | float or null | 条件必填 | 限价委托价格；order_type=market 时可为 null |
| risk_profile_hash | string | ✅ | 风险摘要哈希，用于版本一致性检查 |
| auth_key_id | string | ✅ | 鉴权 key 标识（真实 key 不得写入 Git） |
| signature | string | ✅ | 请求签名 HMAC-SHA256（Base64 编码） |
| delivery_attempt | integer | ✅ | 投递次数，初始 1，重试递增；超过 3 告警 |

---

## 幂等规则

- 主键：`signal_id`
- 辅助校验维度：`source_system + strategy_version + sequence_no`

## TTL 规则

- 唯一判定口径：`expires_at`
- 不接受未填 expires_at 的裸信号

## 鉴权规则

- 必须同时具备 `auth_key_id` 与 `signature`
- 真实鉴权密钥只能作为运行时 Secret 注入，不得写入 Git

## 风险摘要规则

- `risk_profile_hash` 必须可与当前 TASK-0009 风控版本对齐
- 哈希值不匹配时返回 422，不投递

---

## 实现约束

1. 实现代码只能落在 `integrations/legacy-botquant/**`
2. 严禁在 bridge 层新增择时、过滤、信号重组逻辑
3. 桥接失败必须与 signal_id + trace_id + source_system 关联留痕
