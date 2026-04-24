# U0 交接单：decision 内部 TqSdk 同步直跑修复

> 时间：2026-04-24  
> 来自：Atlas  
> 任务：TASK-0127

## 完成情况

decision 内部 TqSdk 正式回测的“长等待超时”问题已完成根因修复并收口。

这次确认的事实是：Air 能正常完成并不是因为它“超时时间更长”，而是因为 Air 生产路径根本没有走 `OnlineBacktestRunner.submit()` 那条异步调度链路；它一直是后台线程直接跑 `runner.run_job_sync()`。decision 之前复用了未被 Air 运行态验证的异步路径，所以表现成“提交成功但结果迟迟不回收”。

## 实际改动文件

1. `services/decision/src/research/tqsdk_backtest_client.py`

## 修复摘要

- `submit_backtest()`：改为只登记 `BacktestJobInput`，不立即启动 runner 内部异步任务
- `poll_result()`：改为 `asyncio.to_thread(self._runner.run_job_sync, job_input)` 同步直跑
- 对外接口保持不变，因此主控脚本无需改动

## 验证结果

### 直接探针

- 策略：`rb_trend_60m_v1`
- 区间：`2024-01-01 ~ 2024-06-30`
- 结果：`29.9s` 返回 `completed`

### 解释口径

- 本轮证明的是“decision 内部 TqSdk 结果回收链已恢复”
- 不是证明“35 品种整条流水线已经全部无问题”

## 当前剩余问题

在 `rb` 的整条 final-only 流水线复跑里，真正剩下的是别的独立问题，而不是 TqSdk：

1. 多个新策略在调优阶段仍会访问 `SHFE.rb_main0`，触发 data API `422`
2. 个别策略的表达式语法仍超出 local formal engine 当前支持范围
3. 个别策略的风险参数本身非法（如负的 `daily_loss_limit`）

这些问题后续应单独拆开处理，不要再混入“TqSdk 超时”口径。

## 收口结论

本批已完成 U0 事后审计补录。decision 内部 TqSdk 正式回测结果回收链已恢复，后续可继续推进 TASK-0127 的剩余流水线问题剥离与 35 品种正式执行。