# lock-U0-20260424-decision-TqSdk同步直跑修复

【任务】TASK-0127 decision 内部 TqSdk 同步直跑修复  
【模式】U0 事后审计锁控  
【记录时间】2026-04-24  
【状态】locked（U0 事后锁回）

## 文件白名单（事后补录）

| 文件 | 操作 | 锁状态 |
|------|------|--------|
| `services/decision/src/research/tqsdk_backtest_client.py` | 修改 | 🔒 locked |

## 变更摘要

- `tqsdk_backtest_client.py`
  - `submit_backtest()` 不再进入 `OnlineBacktestRunner.submit()` 异步调度链路
  - `poll_result()` 改为 `asyncio.to_thread(self._runner.run_job_sync, job_input)` 同步直跑
  - 新增 `_pending_jobs` 暂存提交参数，保持现有调用接口不变

## 验收摘要

- 探针策略：`rb_trend_60m_v1`
- 验证区间：`2024-01-01 ~ 2024-06-30`
- 修复前：长等待表现为 timeout failed
- 修复后：`29.9s` 返回 `status=completed`

## 运行态说明

- Air 现网正式回测口径是“后台线程 -> `runner.run_job_sync()`”
- decision 本次已回归相同执行模型
- 本次锁控仅覆盖 decision 内部 TqSdk 回收链，不覆盖其余 YAML / 数据 / 调优失败项

## 说明

- 本次锁控为 U0 事后补录，不经 lockctl Token 流程
- 修复已完成本地真实探针验证
- 后续若继续修改 decision 业务代码，应回归标准流程预审 + Token