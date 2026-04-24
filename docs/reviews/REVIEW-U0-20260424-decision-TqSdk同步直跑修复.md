# REVIEW-U0-20260424 事后审计

【任务】TASK-0127 decision 内部 TqSdk 同步直跑修复  
【模式】U0 事后审计  
【审计时间】2026-04-24  
【审计人】Atlas  
【结论】✅ 通过

## 1. 边界合规性

- [x] 单服务范围：全部业务改动仅在 `services/decision/` 内
- [x] 未触及 P0 保护区：`shared/contracts/**`、`shared/python-common/**`、`.github/**`、`WORKFLOW.md` 未涉及
- [x] 未触及 P2 区域：`docker-compose.dev.yml`、任一 `.env.example` 未涉及
- [x] 未跨服务 import
- [x] 未修改永久禁区：`runtime/**`、`logs/**`、真实 `.env` 未纳入本批 diff

## 2. 修复必要性

| 修复项 | 必要性 | 最小化评估 |
|--------|--------|-----------|
| decision 内部 TqSdk 回收链改为同步直跑 | ✅ 必要 | 不改则 `poll_result()` 长等待仍会挂在未验证异步链路上 |
| 保留 `submit_backtest/poll_result` 对外接口不变 | ✅ 必要 | 上游主控脚本无需改动，避免扩大回归面 |
| 用 `BacktestJobInput` 暂存待执行任务 | ✅ 必要 | 仅替换内部调度模型，不改业务参数语义 |

## 3. 根因确认

1. Air backtest 服务生产路径是后台线程直接执行 `runner.run_job_sync(job_input)`。
2. decision 内部客户端走的是 `runner.submit()` → `asyncio.create_task()` → `wait_for_job()` 的异步链路。
3. `runner.py` 和 `session.py` 本身不是分叉实现，真正差异在“调用方式”而不是“引擎代码内容”。
4. Air 从未在生产路径中验证 `submit/_execute/_semaphore/wait_for_job` 这条链路，因此 decision 复用该路径后，表现为 TqSdk 任务已提交但结果长期不返回。
5. 所谓“超时”只是外层症状，根因是 decision 走错了 Air 未经运行态验证的调度模型。

## 4. 验证证据

### 4.1 探针验证

| 项目 | 结果 |
|------|------|
| 策略 | `rb_trend_60m_v1` |
| 窗口 | `2024-01-01 ~ 2024-06-30` |
| 等待上限 | `600s` |
| 实际耗时 | `29.9s` |
| 返回状态 | `completed` |

### 4.2 回收结果

- `task_id = tqsdk-strategy-105868df0-1`
- `summary.status = completed`
- formal_report_v1 已成功返回

### 4.3 额外说明

- 本次强制 `final-only` 的整条 rb 流水线复跑中，最终没有再次进入 TqSdk 步骤，原因是其余候选策略在本地回测 / 调优阶段已因 `SHFE.rb_main0` 422、表达式兼容、风险参数非法等问题提前出池。
- 因此“探针 completed”已足够证明本轮 U0 修复命中了 TqSdk 结果回收根因；剩余失败项属于其他独立问题，不应再归因到 TqSdk 超时。

## 5. 风险评估

- 回归风险：低。仅替换 `tqsdk_backtest_client.py` 的内部执行模型，对外接口未变。
- 运行风险：低。修复后执行模型与 Air 现网正式回测路径一致。
- 剩余风险：中低。35 品种流水线仍存在若干策略生成 / YAML 兼容 / `rb_main0` 数据取数问题，但这些已与本次 TqSdk 回收链修复解耦。

## 6. 审计结论

本轮修复满足“单服务、最小必要、无越界、可验证”的 U0 收口要求。decision 内部 TqSdk 正式回测结果回收链已恢复，与 Air 现网执行口径重新对齐，允许进入事后锁回与任务账本收口。