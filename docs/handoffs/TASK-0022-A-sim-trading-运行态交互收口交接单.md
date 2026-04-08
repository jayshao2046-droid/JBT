# TASK-0022-A sim-trading 运行态交互收口交接单

【签名】模拟交易 Agent
【时间】2026-04-08
【设备】MacBook
【状态】终审阻断二次收口已完成并回交；等待项目架构师终审

## 任务信息

- 任务 ID：TASK-0022-A
- 所属任务：TASK-0022
- 执行范围：仅限批次 A 五个白名单文件
- 批次目标：自动补齐 futures-only + 主卡片 50 万口径 + L2 说明收口

## 终审二次收口状态

1. 本次回合仅处理 `REVIEW-TASK-0022-A` 的 3 个阻断点，不扩白名单、不扩功能：`operations/page.tsx` stale closure、`intelligence/page.tsx` 范围外 hunk 清理、`router.py` 非 A 批 runtime hunk 回退。
2. 基于已确认 active 的 `TASK-0022-A` 当前轮次 token，本回合已完成 3 项最小回修：
	- `operations/page.tsx` 为 `availableContracts`、`contractInput`、`orderParams.contract` 增加当前态 ref，`poll` 改读当前 state，消除 stale closure。
	- `intelligence/page.tsx` 清理 `dailyPnlMap`、历史清空、日历盈亏着色及相关额外逻辑，只保留 A 批要求的 L2 黄线 / 红线说明集中展示。
	- `router.py` 回退默认 `ctp_md_front` / `ctp_td_front`、`ctp_app_id`、`ctp_auth_code`、连接成功通知去重等非 A 批 runtime hunk，仅保留 `/api/v1/account` 的 `local_virtual + ctp_snapshot` 语义。
3. `simnow.py` 的 futures-only 修复与 `tests/test_console_runtime_api.py` 的账户 / 非期货过滤覆盖均保留，未回退已通过项。
4. 当前已完成终审阻断二次收口并回交项目架构师终审；`TASK-0022-A` 仍待终审与锁回，`TASK-0022-B` 继续锁定。

## 完成动作

1. 在 `services/sim-trading/src/gateway/simnow.py` 的合约发现链路按 `ProductClass=Futures` 过滤非期货，并补齐郑商所 3 位月份解析，避免 `MA605P2650` 一类期权样式代码进入近月发现链路。
2. 在 `services/sim-trading/src/api/router.py` 将 `/api/v1/account` 收口为 `local_virtual` 与 `ctp_snapshot` 两层结构，固定主口径为本地虚拟盘总本金 50 万，CTP 数值只保留为次级快照。
3. 在 `services/sim-trading/sim-trading_web/app/operations/page.tsx` 收口快速下单自动补齐为期货候选，并把账户展示改为“50 万主卡片 + CTP 快照”语义。
4. 在 `services/sim-trading/sim-trading_web/app/intelligence/page.tsx` 将 L2 黄线 / 红线说明集中到曲线下方同一视觉组，并明确“暂停新开仓 / 强制平仓并锁定交易”触发动作。
5. 在 `services/sim-trading/tests/test_console_runtime_api.py` 补齐账户接口结构与非期货过滤关键逻辑的自动化覆盖。
6. 本批未扩展到 `shared/contracts/**`、`services/sim-trading/.env.example`、部署文件或 `TASK-0022-B` 的日志查看范围。

## 修改文件

1. `services/sim-trading/src/api/router.py`
2. `services/sim-trading/src/gateway/simnow.py`
3. `services/sim-trading/sim-trading_web/app/operations/page.tsx`
4. `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
5. `services/sim-trading/tests/test_console_runtime_api.py`

## 验证结果

1. `get_errors` 已覆盖 5 个白名单业务文件，结果均为 `No errors found`。
2. `PYTHONPATH=. ../../.venv/bin/pytest tests/test_console_runtime_api.py tests/test_health.py tests/test_ctp_notify.py -q` 结果为 `6 passed, 4 warnings`。
3. 4 条 warning 均为既有 FastAPI `on_event` deprecation 提示，不属于本批新增阻断。
4. 本批验收口径已对齐：自动补齐链路不再让非期货合约进入近月发现，主卡片不再直接使用 CTP `balance` 充当系统主权益，L2 说明完成集中化收口且未新增风控规则。
5. 本批未触碰 `shared/contracts/**`、`.env.example`、`docker-compose.dev.yml` 与其他白名单外业务文件。

## 待审问题

1. 当前 `/api/v1/account` 的 `local_virtual` + `ctp_snapshot` 结构仅作为 sim-trading 单服务运行态收口口径；若后续要升级为跨服务契约，仍需单独发起 P0 补充预审。
2. `TASK-0022-B` 尚未签发，`src/main.py` 与最小只读日志查看能力不在本批终审范围内；请按 `TASK-0022-A` 五文件白名单定向核验。
3. 当前交接单仅覆盖 `TASK-0022-A` 已完成结果；若工作树中存在其他 sim-trading 改动，不应混入本批终审与锁回结论。

## 向 Jay.S 汇报摘要

1. `TASK-0022-A` 已按五文件白名单完成终审阻断二次收口：`operations/page.tsx` stale closure 已修、`intelligence/page.tsx` 范围外 hunk 已清、`router.py` 非 A 批 runtime hunk 已回退。
2. 本批静态与测试校验已完成：5 个白名单文件 `get_errors = 0`，指定 `pytest` 结果为 `6 passed, 4 warnings`。
3. futures-only 修复与 `/api/v1/account` 的 `local_virtual + ctp_snapshot` 语义已保留；当前已回交项目架构师终审，`TASK-0022-B` 是否启动仍待 Jay.S 决定。

## 下一步建议

1. 请项目架构师对 `TASK-0022-A` 重新执行定向终审；若通过，立即锁回当前 5 文件白名单。
2. `TASK-0022-A` 终审通过并锁回后，再由 Jay.S 决定是否签发 `TASK-0022-B` 的 P1 Token，继续最小只读日志查看。
3. `TASK-0017` 继续保持“已部署到 Mini，待开盘验证行情 / 成交回传”的运行态观察，不与本批混并处理。