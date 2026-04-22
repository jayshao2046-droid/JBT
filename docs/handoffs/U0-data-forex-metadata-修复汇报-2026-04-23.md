# U0 交接单：外汇日线元数据修正

> 时间: 2026-04-23  
> 来自: Atlas  
> 任务: TASK-P1-20260423B

## 完成情况

外汇日线（forex）3项元数据修正已完成，Mini 验证通过，Jay.S 已确认成功。

**改动文件**: `services/data/src/main.py`

1. `SOURCE_SCHEDULE_HINTS["forex"]`: `"0 6 * * *"` → `"20 17 * * 1-5"`（工作日 17:20）
2. `SOURCE_PROVIDER_HINTS["forex"]`: `"yfinance"` → `"Tushare"`（实际使用 Tushare Pro fx_daily）
3. `SOURCE_DELAY_THRESHOLDS["forex"] = 25.0`（防止工作日17:20采集后次日early morning误标delayed）

## 全面核查上下文

本修复来自对外汇日线采集器的主动全面核查。核查顺序：
1. TASK-P1-20260423（shipping delayed误标）→ 已完成
2. TASK-P1-20260423B（forex元数据）→ 本任务，已完成
3. 下一项：CFTC持仓报告核查（进行中）
