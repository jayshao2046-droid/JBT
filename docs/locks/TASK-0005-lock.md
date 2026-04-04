# TASK-0005 Lock 记录

## Lock 信息

- 任务 ID：TASK-0005
- review-id：REVIEW-TASK-0005-A / REVIEW-TASK-0005-B / REVIEW-TASK-0005-C
- 阶段：全量因子接入与模板解冻：批次 A、批次 B、批次 C 均已完成、终审通过并已锁回；TASK-0005 全三批次闭环
- 执行 Agent：
  - 项目架构师（P-LOG 治理文件）
  - 回测 Agent（P1 业务文件，已签发、已执行并已锁回）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `services/backtest/` 首批 5 文件（P1 区）：Jay.S 已为回测 Agent 签发单 Agent、单任务、文件级 P1 Token
    - token_id：tok-b2422733-d465-4bef-98b4-516ff3628fc1
    - 签发时间：2026-04-04 02:30:05 +0800
    - 有效期：30 分钟
    - 失效时间：2026-04-04 03:00:05 +0800
  - `services/backtest/` 首批 5 文件同范围 replacement token：用于补齐真实 lockback 记录，不扩展白名单
    - replacement token_id：tok-a6e29fe8-4e49-4019-9b06-1b2c98bc8eae
    - issue 时间：2026-04-04 02:57:40 +0800（时间戳：1775242660）
    - review-id：REVIEW-TASK-0005-A
    - notes：TASK-0005 批次A补签用于终审后锁回；范围不变；用于修复缺失 lockctl 记录后的闭环
  - `services/backtest/` 批次 B 5 文件（P1 区）：Jay.S 已为回测 Agent 签发单 Agent、单任务、文件级 P1 Token
    - token_id：tok-83f5a10a-f9d5-45c9-9c49-574ef5797460
    - issue 时间：2026-04-04 11:21:56 +0800（时间戳：1775272916）
    - review-id：REVIEW-TASK-0005-B
    - 失效时间：2026-04-04 11:51:56 +0800（时间戳：1775274716）
    - notes：TASK-0005 批次B：执行链接入与 runner 接入；generic strategy 升级执行路径；保持 FC-224 不回退
    - lockback 结果：approved
    - lockback 摘要：TASK-0005 批次B完成，自校验通过，执行锁回
    - 当前状态：locked

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0005-backtest-全量因子接入与模板解冻预审.md`
2. `docs/reviews/TASK-0005-review.md`
3. `docs/locks/TASK-0005-lock.md`
4. `docs/rollback/TASK-0005-rollback.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 批次 A 业务文件白名单（已签发并锁回）

1. `services/backtest/src/backtest/factor_registry.py`
2. `services/backtest/src/backtest/strategy_base.py`
3. `services/backtest/src/backtest/generic_factor_strategy.py`
4. `services/backtest/tests/test_factor_registry_baseline.py`
5. `services/backtest/tests/test_generic_strategy_loading.py`

## 批次 B 业务文件白名单（已签发并锁回）

1. `services/backtest/src/backtest/runner.py`
2. `services/backtest/src/backtest/result_builder.py`
3. `services/backtest/src/backtest/generic_factor_strategy.py`
4. `services/backtest/tests/test_generic_strategy_execution.py`
5. `services/backtest/tests/test_fc_224_execution_trace.py`

## 当前继续锁定的相关文件

1. `services/backtest/src/backtest/strategy_base.py`
2. `services/backtest/src/backtest/factor_registry.py`
3. `services/backtest/src/backtest/fc_224_strategy.py`
4. `services/backtest/V0-backtext 看板/**`
5. `shared/contracts/**`
6. `docker-compose.dev.yml`
7. `services/backtest/.env.example`
8. 其他全部非白名单文件

## 锁控说明

1. 批次 A 首批 5 文件白名单执行已完成；replacement token 仅用于补齐同范围真实 lockback 记录，不扩展任何文件范围。
2. 原始 P1 Token 自 `2026-04-04 02:30:05 +0800` 生效，原失效时间为 `2026-04-04 03:00:05 +0800`；replacement token 已于 `2026-04-04 02:57:40 +0800` 完成同范围 lockback。
3. 批次 B 继续归属 TASK-0005，不新开任务号；本轮冻结白名单仅限 `runner.py`、`result_builder.py`、`generic_factor_strategy.py`、`test_generic_strategy_execution.py`、`test_fc_224_execution_trace.py` 五文件，不回头改批次 A 已锁回的 `factor_registry.py` 基线。
4. 批次 B 新 Token 已于 `2026-04-04 11:21:56 +0800` 正式签发并生效，并已据此完成真实 lockback；上述 5 文件当前已恢复锁定，白名单外文件始终锁定。
5. 批次 B 已完成 agent 自校验、项目架构师代码终审与真实 lockback；当前状态统一为“已完成、自校验通过、终审通过、已锁回”。
6. 若后续必须新增第 6 个文件，仍需重新补充预审并申请新的 Token；本轮不包含目录级解锁、delete Token、rename Token、move Token，也不扩展到看板、contracts、docker、`.env.example` 或其他服务。
7. 项目架构师已于 `2026-04-04 11:44:42 +0800` 完成批次 B 代码终审；随后已按原批次 B token 完成真实 lockback，结果 `approved`，review-id `REVIEW-TASK-0005-B`，当前状态 `locked`，无需补签 replacement token。
8. 批次 C 尚未开始；`factor_registry.py`、`strategy_base.py`、`fc_224_strategy.py`、`services/backtest/V0-backtext 看板/**`、`shared/contracts/**`、`docker-compose.dev.yml`、`services/backtest/.env.example` 与其他全部非白名单文件继续冻结。

## 当前状态

- 预审状态：批次 A、批次 B 均已通过并锁回
- Token 状态：批次 A replacement token 已签发并完成 lockback；批次 B Token 已完成真实 lockback，当前状态为 locked；**批次 C 已预审，Token 待签发**
- 解锁状态：批次 A 已完成；批次 B 白名单 5 文件已完成写入、自校验、终审与锁回；批次 C 预审已完成，待 Jay.S 签发 Token

## 批次 C 业务文件白名单（待签发）

1. `services/backtest/src/backtest/generic_factor_strategy.py`
2. `services/backtest/tests/test_factor_registry_coverage.py`（新增）

## 批次 C 锁控说明

1. 批次 C 已完成预审（2026-04-04），冻结白名单为上述 2 文件，在 WORKFLOW 5 文件上限内。
2. 批次 C 继续归属 TASK-0005，不新开任务号；Token 范围应冻结为上述 2 文件，review-id 应为 `REVIEW-TASK-0005-C`。
3. 本批修改目标唯一：`generic_factor_strategy.py` 的 `_NON_DIRECTIONAL_KEYS` 集合加入 `"garmanKlass"`；`test_factor_registry_coverage.py` 新增 33 项因子接线完整性覆盖测试。
4. 批次 C Token 尚未签发；在 Jay.S 签发 Token 前，回测 Agent 不得写入上述 2 文件；`factor_registry.py`、`strategy_base.py`、`fc_224_strategy.py`、`runner.py`、`result_builder.py`、看板、contracts、docker、`.env.example` 与其他全部非白名单文件继续锁定。
5. 若后续必须新增第 3 个文件，仍需重新补充预审并申请新的 Token；本批次不包含目录级解锁、delete Token、rename Token、move Token，也不扩展到看板、contracts、docker、`.env.example` 或其他服务。

## 批次 C 当前状态

- 预审状态：批次 C 预审通过（2026-04-04），冻结白名单 2 文件
- Token 状态：已签发，review-id `REVIEW-TASK-0005-C`，token_id `tok-4d65bb9a-a51c-40bb-b50d-4dd804294d13`
- 代码终审状态：**代码终审通过（2026-04-04）**
- lockback 结果：approved
- lockback 摘要：GarmanKlass接线修复，33项因子全覆盖测试通过，执行锁回
- 锁回时间：2026-04-04
- 当前锁态：locked
- 批次 C 统一结论：**已完成、自校验通过、终审通过、已锁回**

## 结论

**TASK-0005 批次 A 已使用 replacement token `tok-a6e29fe8-4e49-4019-9b06-1b2c98bc8eae` 完成真实 lockback；review-id 为 `REVIEW-TASK-0005-A`，结果 `approved`，当前状态 `locked`。批次 B 已由 Jay.S 使用 token `tok-83f5a10a-f9d5-45c9-9c49-574ef5797460` 完成真实 lockback；review-id 为 `REVIEW-TASK-0005-B`，结果 `approved`，lockback 摘要为 `TASK-0005 批次B完成，自校验通过，执行锁回`，当前状态 `locked`。批次 C 已由 Jay.S 使用 token `tok-4d65bb9a-a51c-40bb-b50d-4dd804294d13` 完成真实 lockback；review-id 为 `REVIEW-TASK-0005-C`，结果 `approved`，lockback 摘要为 `GarmanKlass接线修复，33项因子全覆盖测试通过，执行锁回`，当前状态 `locked`。TASK-0005 全三批次（A、B、C）统一结论均为"已完成、自校验通过、终审通过、已锁回"；33 项官方因子在 generic strategy 中完整接线，GarmanKlass 接线缺口已收口，两集合互斥已验证，既有回归无回退；TASK-0005 全任务正式闭环。`strategy_base.py`、`factor_registry.py`、`fc_224_strategy.py`、看板、contracts、docker、`.env.example` 与其他非白名单文件继续锁定，等待下一个任务的独立预审与 Token。**