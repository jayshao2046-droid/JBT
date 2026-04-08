# TASK-0022 sim-trading 运行态交互预审交接单

【签名】项目架构师
【时间】2026-04-08
【设备】MacBook

## 一、交接目标

为模拟交易 Agent 提供 `TASK-0022` 的正式预审结论、批次白名单与 Token 申请清单；当前仅允许据此准备执行，不得越权写代码。

## 二、当前结论

1. `TASK-0022` 已独立成立，不并入 `TASK-0017`。
2. 本轮归属明确冻结为 `services/sim-trading/**` 单服务范围。
3. `TASK-0015` 的 dashboard / `/tmp` 临时看板历史口径不适用于当前仓内真实运行的 sim-trading 控制台。
4. 当前 4 项问题已拆为 2 个 P1 批次：A 为自动补齐 + 账户口径 + L2 说明收口，B 为最小只读日志查看。

## 三、批次清单

### 批次 A：自动补齐 + 账户口径 + L2 说明收口

- 执行 Agent：模拟交易 Agent
- 保护级别：P1
- 是否需要 Token：需要 P1
- 是否可并行：否

#### 白名单

1. `services/sim-trading/src/api/router.py`
2. `services/sim-trading/src/gateway/simnow.py`
3. `services/sim-trading/sim-trading_web/app/operations/page.tsx`
4. `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
5. `services/sim-trading/tests/test_console_runtime_api.py`

#### 目标

1. 自动补齐仅保留期货合约候选。
2. 主卡片展示“本地虚拟盘总本金 50 万”，真实 CTP 余额降为快照信息。
3. L2 红线 / 黄线说明居中收口并写清触发动作。

### 批次 B：最小只读日志查看

- 执行 Agent：模拟交易 Agent
- 保护级别：P1
- 是否需要 Token：需要 P1
- 是否可并行：否

#### 白名单

1. `services/sim-trading/src/main.py`
2. `services/sim-trading/src/api/router.py`
3. `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
4. `services/sim-trading/tests/test_log_view_api.py`

#### 目标

1. 增加当前服务最近日志的只读查看能力。
2. intelligence 页“查看日志”不再继续 toast 占位。
3. 不提供路径输入、目录浏览、下载、清空或写操作。

## 四、执行约束

1. A / B 两批不可并行，因为共享 `router.py` 与 `intelligence/page.tsx`。
2. 当前不解锁 `shared/contracts/**`；若执行中要求修改正式契约，必须回交补充预审。
3. 当前不解锁 `services/sim-trading/.env.example`；若执行中要求把 50 万本金变成配置项，必须回交 P0 补审。
4. 当前不解锁任何部署文件；禁止把日志查看或主卡片改动混入 `TASK-0017` / `TASK-0020`。

## 五、向 Jay.S 汇报摘要

1. 已完成 `TASK-0022` 正式预审建档；当前 4 项问题不归 `TASK-0017`，而是独立新建为 sim-trading 单服务任务。
2. 当前建议拆为 2 个 P1 批次：A（5 文件）处理自动补齐 / 账户口径 / L2 说明；B（4 文件）处理最小只读日志查看。
3. 两批都不需要 P0 Token；若后续要碰 `.env.example` 或 `shared/contracts/**`，需另起 P0 补充预审。
4. 批次 B 当前最小方案限定为“进程内最近日志只读查看”；若要历史文件日志或下载能力，范围会膨胀，需重新补审。

## 六、下一步建议

1. 先由 Jay.S 决定是否立即签发 `TASK-0022-A` 的 P1 Token。
2. 批次 A 完成并回交自校验后，再决定是否签发 `TASK-0022-B` 的 P1 Token。
3. 在 Jay.S 未确认前，不派发模拟交易 Agent 进入 `TASK-0022` 代码写入。