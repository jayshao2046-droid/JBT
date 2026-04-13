# REVIEW-TASK-0083-PRE — 决策端全闭环收尾预审

| 字段 | 值 |
|------|------|
| 审核ID | REVIEW-TASK-0083-PRE |
| 任务ID | TASK-0083 |
| 审核人 | Atlas（项目架构师代审） |
| 时间 | 2026-04-13 |
| 结论 | ✅ 通过 |

## 预审范围

### Part A — LLM Pipeline 与研究中心集成
- **服务边界**：decision 内部，不新增跨服务依赖
- **数据读取**：通过已有 `data_service_url`（settings.py L39）拉取 K 线，走标准 HTTP API，不跨服务 import
- **研究中心接入**：复用已有 factor_loader / sandbox_engine / stock_pool 的 Python import，均在 decision 服务内部
- **风险**：低。仅修改 5 个已有文件（均为 TASK-0081 新建文件），不影响其他路由

### Part B — CK1~CK3 因子同步
- **服务边界**：涉及 P0 保护区 `shared/python-common`，需 Token 授权
- **变更范围**：新建 `shared/python-common/factors/` 目录（3 文件），修改 decision factor_loader + backtest factor_registry
- **风险**：中。shared/python-common 是 P0 区域，但本次仅新增文件（registry + sync工具），不修改现有 shared 代码
- **校验**：因子 hash 校验为只读比对，不改变因子计算逻辑

### Part C — Bug 修复
- **Bug 2.1**：SignalDispatcher._dispatched 加 FIFO 淘汰，纯内部修改，无 API 变更
- **Bug 1.1**：ctp_disconnect() 补 _connect_lock，仅 sim-trading router.py 1 处修改

## 白名单冻结（12 文件）

```
services/decision/src/llm/pipeline.py
services/decision/src/llm/prompts.py
services/decision/src/llm/client.py
services/decision/src/api/routes/llm.py
services/decision/tests/test_llm_pipeline.py
shared/python-common/factors/__init__.py
shared/python-common/factors/registry.py
shared/python-common/factors/sync.py
services/decision/src/research/factor_loader.py
services/backtest/src/backtest/factor_registry.py
services/decision/src/core/signal_dispatcher.py
services/sim-trading/src/api/router.py
```

## 依赖确认

- data 服务 bars API（C0-1 TASK-0050 已投产） → decision 通过 HTTP 拉取
- 研究中心全链路（CA/CB 全闭环） → decision 内部 import
- sim-trading _connect_lock 已存在（router.py L29） → 复用

## 结论

白名单冻结 12 文件，覆盖 Part A/B/C 三部分。无 Phase 顺序变更、无服务归属变更、无新增跨服务 import。通过预审。
