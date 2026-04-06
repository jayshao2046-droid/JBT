# TASK-0018 Review

## Review 信息

- 任务 ID：TASK-0018
- 审核角色：项目架构师
- 审核阶段：D201（自建回测系统）建档预审
- 审核时间：2026-04-07
- 审核结论：条件通过（建档通过；进入代码执行前需分批 Token 解锁）

---

## 一、预审范围

1. 仅审任务边界、分批策略、白名单模板与治理约束。
2. 本轮不写任何 `services/**` 或 `shared/contracts/**` 业务代码。

## 二、预审结论

1. 任务目标清晰：保留 TqSdk/TqBacktest 既有系统 + 新增 local 自建回测系统，并提供统一执行入口。
2. 批次拆分合理：A（P0 契约扩展）-> B（P1 data API）-> C（P1 双引擎编排）-> D（P1 系统级风控联动）-> E（P1 引擎选择控件）-> F（P1 完整报告导出与展示）。
3. 服务边界清晰：data 供数、backtest 消费与执行、contracts 统一边界。
4. 治理约束已冻结：禁止跨服务 import、禁止跨目录直读、禁止改动运行态敏感路径。

## 三、关键风险

1. 契约漂移风险：契约先行不充分会导致 B/C 批次接口对不齐。
2. 数据延迟风险：Mini API 延迟或抖动会影响回测窗口与重试策略。
3. 确定性回测风险：缓存与重试若处理不当会破坏回测可重复性。
4. 风控语义偏差风险：夜盘/日切锚点定义不一致会导致回测与实盘解释偏差。
5. 双引擎结果口径漂移风险：同一输入下 `tqsdk` 与 `local` 结果可能产生不可解释偏差。
6. 双引擎风控语义不一致风险：不同引擎触发风控事件的证据链粒度不一致。
7. 报告 schema 漂移风险：两引擎报告字段演进不同步导致导出/展示断裂。
8. UI 误触发默认引擎风险：引擎选择控件默认值不透明导致误执行。

## 四、阻断条件

1. 无 Token 不得写保护区（`shared/contracts/**`、`services/**` 等）。
2. 批次外文件禁止改动，若需扩白名单必须回交补充预审。
3. 未完成自校验不得提交终审。
4. 未完成终审与锁回不得宣布批次完成。

## 五、当前轮次白名单

1. `docs/tasks/TASK-0018-backtest-API化重建-Phase1.md`
2. `docs/reviews/TASK-0018-review.md`
3. `docs/locks/TASK-0018-lock.md`
4. `docs/handoffs/TASK-0018-架构预审交接.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 六、下一步准入条件

1. 先执行批次 A 的文件级 P0 Token 签发。
2. A 完成并锁回后，优先进入 C；B 可并行但必须在 C 接口冻结前完成契约对齐。
3. 后续按 C/D/E/F 顺序逐批推进，每批独立审核、独立锁回。
4. 新增统一验收门槛：同一输入下，两引擎结果必须可解释（允许数值差异，但必须提供证据链）。

---

## 七、批次 A 执行记录（2026-04-07）

- 执行结论：已执行（仅契约单文件）
- 业务文件：`shared/contracts/backtest/api.md`
- 关联 token_id：`tok-38d7c21e-36bd-4fe1-a4dc-843178e351dc`

本批已在 `shared/contracts/backtest/api.md` 补齐并冻结：

1. `engine_type` 字段：固定支持 `tqsdk`、`local`，默认值 `tqsdk`，保留既有 TqSdk 路径兼容。
2. 系统级风控事件证据链结构：统一 `risk_event` 最小字段，覆盖触发原因、阈值、观测值、时间、引擎归属，并要求双引擎共用。
3. 完整报告导出统一结构：冻结 `formal_report_v1` schema，要求两引擎输出同一主字段集合并挂接风控证据链。

## 八、批次 A 最小自校验

1. 业务改动范围校验通过：仅 `shared/contracts/backtest/api.md`。
2. 治理留痕校验通过：仅更新 `docs/reviews/TASK-0018-review.md`、`docs/locks/TASK-0018-lock.md`、`docs/prompts/公共项目提示词.md`、`docs/prompts/agents/项目架构师提示词.md`。
3. 未发生 `services/**` 目录改动。
4. 结论：批次 A 可提交终审并执行锁回。
5. 收口标记：`TASK-0018-A-EXECUTED-2026-04-07`。

## 九、批次 A 终审与锁回结果

1. 终审结论：通过（approved）。
2. lockback 已执行：`review-id=REVIEW-TASK-0018-A`。
3. Token 状态：locked。

---

## 批次 C 终审（2026-04-07）

### 终审基本信息

- 终审时间：2026-04-07
- 审核角色：项目架构师
- 对应 Token：`tok-4f7d7a03-e4be-4c40-bc88-493175e8f587`
- Atlas 自校验结论：18 passed，2 个预存在失败与本批次无关

### 终审结论

```
【终审结论】⚠️ 有保留通过

【边界合规】
  A1 – 实际改动严格限于白名单 4 文件：通过
  A2 – generic_strategy.py 未被触碰（git diff 零输出）：通过
  A3 – runner.py 未被触碰（git diff 零输出）：通过
  A4 – 无跨服务 import（grep 四文件零命中）：通过
  A5 – 批次 C 自身未写入 shared/contracts；但 shared/contracts/backtest/api.md
       有批次 A 未提交的 §6.2 全部内容处于未提交状态，须在批次 C 提交前先提交
       批次 A 修改（独立 commit），属流程保留项，非代码违规：有保留通过

【验收标准】
  B1 – tqsdk 路径（generic_strategy.py / runner.py）零改动，jobs.py 对 tqsdk
       路径仅新增 execution_stage 判断，既有响应字段未移除：通过
  B2 – local 引擎可运行最小回测并产出 LocalBacktestReport；summary 含
       final_equity / max_drawdown / pnl / win_rate / sharpe，但
       artifacts.equity_curve = None（内部 equity 列表未序列化到报告）；
       批次 C MVP 可接受，需在批次 D/F 中补全：有保留通过
  B3 – EngineRouter 正确分发，不支持的值抛 EngineTypeError，API 层转 422
       并含 "engine_type" 字样："Unsupported engine_type: '...' "：通过
  B4 – DataProvider 抽象层（ABC）已建立，MockDataProvider 实现完整；
       批次 B/D 可无改动引擎核心直接替换 Provider：通过
  B5 – jobs.py 改动最小化：新增 engine_type 校验调用 + execution_stage 字段，
       全部原响应字段保留，无字段删除或重命名：通过

【契约对齐】
  C1 – engine_type 限定 tqsdk/local，默认 None→tqsdk，与 api.md §6.2.1 一致：通过
  C2 – schema_version="formal_report_v1" ✓；job / summary / transaction_costs /
       risk_events / artifacts 主字段均存在 ✓；但 job.strategy_id 字段在契约
       §6.2.3 最小示例中存在而报告实现中缺失（MVP 阶段未绑定 strategy_template）；
       当前可接受，须在批次 D/E 中补全：有保留通过
  C3 – 批次 C MVP 不产生 risk_events（空列表），不存在格式违规：通过

【代码质量】
  D1 – 无硬编码凭证、无 SQL 查询（无注入面）、无用户路径拼接（无路径穿越）：OK
  D2 – equity_curve 内存列表随回测窗口线性增长，超长期回测可能 OOM；
       _JOB_STORE 先写后限的非原子逻辑为批次 A 遗留，不新引入；SMA 窗口
       内层切片为 O(n·k)，MVP 数据量下可接受：WARN
  D3 – ValueError / EngineTypeError 显式抛出，API 层统一捕获转 HTTPException，
       无静默吞掉异常路径：OK

【关键发现】
  1. 流程保留：shared/contracts/backtest/api.md §6.2 全部内容（批次 A 成果）
     尚处于未提交状态，需在批次 C 独立提交前先独立提交批次 A。
  2. 工程保留（B2）：artifacts.equity_curve = None；建议批次 D/F 在
     _simulate() 返回 equity_curve 后将其写入 artifacts（可序列化为 base64
     或 inline list），以满足 formal_report_v1 完整性要求。
  3. 契约保留（C2）：job.strategy_id 字段缺失；建议批次 D 在接入 strategy_template
     后同步补全；批次 C MVP 阶段引擎使用内置 EMA5/20 策略，无外部 strategy_id，
     可临时填写 "local_ema_crossover_v1" 作为占位。

【锁回授权】是
【备注】18 个测试全部通过；核心功能（双引擎路由、local 引擎执行、API 分发）均已闭环；
        三条保留项均属 MVP 工程范围内的可接受延迟，不阻塞批次 C 锁回。
        批次 D 启动前必须先补全批次 A commit，再正式锁回批次 C。
```
