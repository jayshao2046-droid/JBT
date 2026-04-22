# U0 事后审计：外汇日线元数据修正

> 执行时间: 2026-04-23  
> 执行模式: U0 直修（Jay.S 明确指令，单服务，非 P0/P2 区域）  
> 执行人: Atlas  
> 关联任务: TASK-P1-20260423B

## 修复内容

| # | 位置 | 修复前 | 修复后 |
|---|------|--------|--------|
| 1 | `SOURCE_SCHEDULE_HINTS["forex"]` | `"0 6 * * *"` | `"20 17 * * 1-5"` |
| 2 | `SOURCE_PROVIDER_HINTS["forex"]` | `"yfinance"` | `"Tushare"` |
| 3 | `SOURCE_DELAY_THRESHOLDS["forex"]` | 缺失（默认13h） | `25.0`（25h，防误标） |

## 验证结果

```
status: success
schedule_expr: 20 17 * * 1-5
data_source: Tushare
age_h: 11.047
threshold_h: 26
```

## U0 约束核验

- [x] 单服务（services/data），无跨服务
- [x] 非 P0/P2 区域（仅改元数据字典，无业务逻辑变更）
- [x] 问题已只读确认后才进入修改
- [x] 已交付 Jay.S 确认成功

## 审计结论

修复通过，符合 U0 边界约束。
