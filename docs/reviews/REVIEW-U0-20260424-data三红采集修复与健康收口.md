# REVIEW-U0-20260424 事后审计

【任务】TASK-U0-20260424 data 三红采集修复与健康收口  
【模式】U0 事后审计  
【审计时间】2026-04-24  
【审计人】Atlas  
【结论】✅ 通过

## 1. 边界合规性

- [x] 单服务范围：全部业务改动在 `services/data/` 内
- [x] 未触及 P0 保护区：`shared/contracts/**`、`shared/python-common/**`、`.github/**`、`WORKFLOW.md` 未涉及
- [x] 未触及 P2 区域：`docker-compose.dev.yml`、任一 `.env.example` 未涉及
- [x] 未跨服务 import
- [x] 未修改永久禁区：`runtime/**`、`logs/**`、真实 `.env` 未纳入本批 diff

## 2. 修复必要性

| 修复项 | 必要性 | 最小化评估 |
|--------|--------|-----------|
| 持仓日报最近交易日回退 | ✅ 必要 | 当天白天无数据时原逻辑必空跑，不改无法恢复 |
| 期权行情最近交易日回退 | ✅ 必要 | 原逻辑与调度器强制 today 叠加，导致连续失败 |
| 外汇日线 `ts_code` 映射修正 | ✅ 必要 | 裸代码不符合 Tushare `fx_daily` 入参要求 |
| 期权调度取消强制 today | ✅ 必要 | 不解除该约束，collector 回退逻辑无法生效 |

## 3. 根因确认

1. `position_collector.py` 默认当天 `trade_date`，交易日白天取不到持仓数据。
2. `options_collector.py` 同样默认当天，且 `data_scheduler.py` 强制注入当天日期，阻断回退。
3. `forex_collector.py` 用 `USDCNH` 等裸代码调用 `pro.fx_daily()`，与 Tushare 的 `*.FXCM` 语义不匹配。
4. Mini API 运行态 `DATA_STORAGE_ROOT=/data`，因此 collectors 面板读的是 `/data` 而不是 `/app/runtime/data`。

## 4. 验证证据

### 4.1 Mini 容器手动采集

| 采集器 | 结果 | 说明 |
|--------|------|------|
| 持仓日报 | `position_daily: 20` | 最近有效交易日回退成功 |
| 期权行情 | `options: 1764` | 最近有效交易日回退成功 |
| 外汇日线 | `forex: 124` | FXCM `ts_code` 映射生效 |

### 4.2 health_check 新鲜度

Mini 容器直接读取 `get_collector_freshness()`：

- `position_daily`: `ok=True`, `age_str=0min`
- `forex`: `ok=True`, `age_str=0min`
- `options`: `ok=True`, `age_str=0min`

### 4.3 用户可见 collectors 面板

`GET /api/v1/dashboard/collectors` 最终返回：

- `position_daily.status = success`
- `forex.status = success`
- `options.status = success`

## 5. 风险评估

- 回归风险：低。改动集中在 3 个采集器的日期 / 代码映射逻辑和 1 个调度器参数传递点。
- 运行风险：低。验证已覆盖 Mini 容器真实调用与用户可见 API 回读。
- 操作风险：中低。后续人工补采若仍写到 `/app/runtime/data`，面板不会更新，因此必须遵守 `/data` 根目录口径。

## 6. 审计结论

本轮修复满足“单服务、最小必要、无降级、可验证”的 U0 收口要求。三项采集链路均已恢复正常采集与正常消费，用户可见红灯已清除，允许进入锁回与独立提交。