# TASK-P1-20260423-data-shipping-delay-误标修复

## 基本信息

| 字段 | 值 |
|------|---|
| 任务 ID | TASK-P1-20260423-data-shipping-delay-误标修复 |
| 优先级 | P1 |
| 类型 | Hotfix — 生产显示错误 |
| 发现时间 | 2026-04-23 |
| 发现人 | Jay.S 全面核查 |
| 服务 | services/data |
| 状态 | 预审中 |

## 问题描述

Dashboard 把"海运物流"采集器误标成 `delayed`，运行日志显示正常（今日 04-23 09:10 已完成采集，120条）。

## 根因分析

`services/data/src/main.py` 中：

```python
_FRESHNESS_THRESHOLDS = {
    ...
    "shipping": 26.0,   # 26小时新鲜度阈值（合理：工作日一次）
    ...
}
SOURCE_DELAY_THRESHOLDS = {
    "futures_eod": 24.0,
    "overseas_minute": 1.0,
    # shipping 未配置 → 默认 threshold_h * 0.5 = 13.0h
}
```

`_collector_status` 逻辑：
- `delay_h` 未配置 → 默认 `26.0 × 0.5 = 13.0h`
- 今日 09:10 采集后，到 22:30 age_h = **13.4h**
- `13.4 > 13.0` → 被标记为 `"delayed"` ← **误判**

实际上 shipping 每工作日只运行一次（09:10），数据在 26h 内都属正常，超过 13h 就告警是过于激进的阈值。

## 修复方案

最小一行修复：`SOURCE_DELAY_THRESHOLDS` 增加 `"shipping": 25.0`

```python
SOURCE_DELAY_THRESHOLDS = {
    "futures_eod": 24.0,
    "overseas_minute": 1.0,
    "shipping": 25.0,   # 工作日一次性任务，25h内不告警；>25h才是真正的延迟
}
```

修复后行为：
- age_h=13.4h → 13.4 > 25.0? No → **success** ✅
- age_h=25.1h → 25.1 > 25.0? Yes → delayed（真正延迟）
- age_h>26.0h → ok=False → failed（完全过期）

## 修改文件

| 文件 | 操作 | 范围 |
|------|------|------|
| `services/data/src/main.py` | 修改 `SOURCE_DELAY_THRESHOLDS` dict，增加1行 | 第204-207行附近 |

## 验收标准

1. `curl http://192.168.31.76:8105/api/v1/dashboard/collectors` → shipping.status = "success"
2. shipping.age_h 约 13.x（未变）
3. 其他采集器状态不受影响

## 影响范围

仅 data 服务 `main.py` 第 204 行配置字典，无逻辑改动，无跨服务影响。
