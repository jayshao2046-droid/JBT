# TASK-0004 Review

## Review 信息

- 任务 ID：TASK-0004
- 审核角色：项目架构师
- 审核阶段：看板阶段预审 + 2026-04-04 Token 签发补充确认 + 2026-04-06 单文件补充预审 + 2026-04-06 单文件补充终审
- 审核时间：2026-04-03；2026-04-04 补充；2026-04-06 补充；2026-04-06 终审
- 审核结论：通过（范围冻结为 `services/backtest/backtest_web/` 内两页收敛；预审最小业务白名单为 3 文件；2026-04-04 已补充确认 Jay.S 实际签发范围收敛为 2 文件，并完成前后端联动语义冻结；2026-04-06 已补充冻结为 `app/agent-network/page.tsx` 单文件百分比交互收口，并已完成终审与锁回）

---

## 一、任务边界核验

1. 任务目标明确：将现有 backtest 看板原型收敛为“策略管理 + 回测详情”两类页面。
2. 任务目录明确：仅限 `services/backtest/backtest_web/`。
3. 本轮明确禁止扩展到：
   - `services/backtest/src/**`
   - `services/backtest/tests/**`
   - `shared/contracts/**`
   - `docker-compose.dev.yml`
   - `services/*` 其他目录
4. 本轮默认不做文件删除，不做目录迁移，不做跨服务实现。

## 二、只读技术结论

1. `app/page.tsx` 当前是 5 个 section 的单页壳层，是本轮导航收敛的唯一必要入口文件。✅
2. `app/agent-network/page.tsx` 当前已对应“策略管理”主页面，是本轮保留页之一。✅
3. `app/operations/page.tsx` 当前已对应“回测详情”主页面，是本轮保留页之一。✅
4. `app/layout.tsx` 当前仅处理字体、metadata 与全局 body 包裹，本轮无需纳入白名单。✅
5. `package.json` 当前依赖已覆盖 Next.js 原型运行所需能力，本轮无需新增依赖或修改脚本。✅
6. `app/command-center/`、`app/intelligence/`、`app/systems/` 当前可保留文件，仅通过停止引用退出本轮视图。✅

## 三、白名单冻结

### 建议签发的 P1 业务文件白名单

1. `services/backtest/backtest_web/app/page.tsx`
2. `services/backtest/backtest_web/app/agent-network/page.tsx`
3. `services/backtest/backtest_web/app/operations/page.tsx`

### 当前不建议纳入的文件

1. `services/backtest/backtest_web/app/layout.tsx`
2. `services/backtest/backtest_web/package.json`
3. `services/backtest/backtest_web/app/command-center/page.tsx`
4. `services/backtest/backtest_web/app/intelligence/page.tsx`
5. `services/backtest/backtest_web/app/systems/page.tsx`

### 不扩白名单的判断依据

1. 首页默认进入“策略管理”可直接在 `app/page.tsx` 内收口。
2. 两个目标页面主体已经存在，本轮不需要额外创建新页面或改全局 layout。
3. 其余页面默认只做“停止引用”，无需删除或修改其文件内容。

## 四、执行 Agent 建议

- **合规默认建议：回测 Agent。**

理由：

1. 目标文件仍位于 `services/backtest/` 目录内。
2. 按当前服务隔离规则，回测目录的业务文件应由回测 Agent 修改。
3. 若 Jay.S 指定看板 Agent 直接写入本目录，则应在 Token 中显式覆盖执行主体，并作为本轮专项例外留痕。

## 五、风险与缓解

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| 顺手把 `layout.tsx`、`package.json` 或其余页面一起改动 | P1 | Token 严格限制为 3 文件；超范围即中止并补充预审 |
| 把“停用页面”误做成删除页面 | P1 | 明确本轮优先停用导航 / 停止引用，不做删除 |
| 以看板需求名义扩展到回测引擎或 Docker | P0 | 预审已冻结边界；任何扩展都需新任务或补充预审 |
| 看板 Agent 直接改 `services/backtest/` 引发服务归属冲突 | P1 | 默认建议回测 Agent；如坚持看板 Agent，需 Jay.S 在 Token 中显式绑定执行主体 |

## 六、预审结论

1. **TASK-0004 预审通过。**
2. **本轮可直接进入 Token 申请准备态。**
3. **预审原建议为单 Agent、单任务、3 文件的 P1 Token；2026-04-04 实际签发结果以第七节补充为准。**
4. **当前公共状态应切换为“TASK-0004 看板阶段已预审，待 Jay.S 签发 Token”。**

## 七、2026-04-04 Token 签发补充确认

1. Jay.S 已于 2026-04-04 为回测 Agent 签发 TASK-0004 当前有效 P1 Token。
2. 本轮有效业务白名单只有 2 个文件：`services/backtest/backtest_web/app/agent-network/page.tsx`、`services/backtest/backtest_web/app/operations/page.tsx`；`services/backtest/backtest_web/app/page.tsx` 不在当前有效 Token 范围内。
3. 前后端联动语义已确认如下：点击策略后默认显示基本信息、策略参数、信号参数、风控参数；合约选择保留并上移；并发上限 KPI 下移到回测按钮下；取消 KPI 收起；扩充当前策略摘要；去掉行情类型与品种专属预设。
4. 若执行中发现必须修改第 3 个业务文件 `services/backtest/backtest_web/app/page.tsx` 或任一后端文件，则当前 Token 立即暂停，必须补充预审。
5. 当前执行口径以本节为准，不得再按“3 文件待签发”旧口径推进。

## 八、2026-04-05 补充预审（主力合约实时源 + 错误提示收口）

1. 补充预审成立，原因是当前问题已超出两页前端范围：
   - `/api/market/main-contracts` 仍来自本地静态兼容清单，导致自动补全与主力映射月份过期。
   - 前端网络层在后端返回 JSON `detail` 对象时仍可能展示为 `[object Object]`。
2. 本轮补充范围仍严格限定在 `services/backtest/` 单服务内，不涉及 `shared/contracts/**`、其他服务、Docker、runtime 目录或真实账本数据。
3. 2026-04-05 补充后建议的最小业务文件集合冻结为 4 个文件：
   - `services/backtest/src/api/routes/support.py`
   - `services/backtest/backtest_web/src/utils/api.ts`
   - `services/backtest/backtest_web/src/utils/strategyPresentation.ts`
   - `services/backtest/tests/test_api_surface.py`
4. 本轮不纳入白名单的文件保持不变，尤其不得顺带扩展到：
   - `services/backtest/src/api/routes/backtest.py`
   - `services/backtest/src/api/routes/strategy.py`
   - `services/backtest/backtest_web/app/page.tsx`
   - `shared/contracts/**`
   - `docker-compose.dev.yml`
5. 验收标准：
   - `/api/market/main-contracts` 优先返回 TqSdk 实时主力清单；若实时查询失败，必须安全回退到本地兼容清单，且响应结构不变。
   - 前端显示的数据源文案能够区分 TqSdk 实时源与本地兼容回退源。
   - 后端若返回对象型错误详情，前端必须展示可读文本，不得再出现 `[object Object]`。
   - 对包含当前月份合约的策略导入与运行链路做回归验证，不得因旧静态主力清单导致错误映射。
6. 建议执行主体仍为：回测 Agent。

## 九、2026-04-05 终审结论（补充范围 4 文件）

1. 本地自校验通过：`services/backtest/src/api/routes/support.py`、`services/backtest/backtest_web/src/utils/api.ts`、`services/backtest/backtest_web/src/utils/strategyPresentation.ts`、`services/backtest/tests/test_api_surface.py` 静态诊断均为 0。
2. 代码级动态回归通过：
   - `/api/market/main-contracts` 可在具备 TqSdk 能力时返回 `tqsdk_realtime_main_contracts`。
   - `/api/market/quotes` 可在具备 TqSdk 能力时返回 `tqsdk_realtime_quotes`。
   - 当实时能力不可用时，两者分别安全回退到 `service_local_compatibility` 与 `service_local`。
3. 前端网络层对象型错误详情已完成文本化处理，补充来源文案已能区分 TqSdk 实时源与本地兼容回退源。
4. 终审结论：通过，无阻断项。
5. 锁回结论：可以立即锁回本轮补充范围 4 个文件。

## 十、2026-04-05 紧急补充预审（正式回测收口 + YAML symbols 解析 + hydration 修复）

1. 补充预审成立，原因是 8103 现网联调已确认出现三类新增阻断问题：
   - 匹配 YAML 的正式回测会以 `Backtest execution failed: 回测结束` 失败收口。
   - `agent-network` 对根级 `symbols:` 列表解析失败，前端误报“YAML 中未找到 symbols”。
   - 页面首屏使用 `new Date()` 直接渲染时间，触发 hydration mismatch。
2. 本轮补充范围仍严格限定在 `services/backtest/` 单服务内，不涉及 `shared/contracts/**`、Docker、其他服务或运行态目录。
3. 经项目架构师紧急补审，最小必要业务文件集合冻结为 3 个业务文件 + 2 个治理文件：
   - `services/backtest/src/backtest/generic_strategy.py`
   - `services/backtest/backtest_web/app/agent-network/page.tsx`
   - `services/backtest/tests/test_generic_strategy_pipeline.py`
   - `docs/reviews/TASK-0004-review.md`
   - `docs/locks/TASK-0004-lock.md`
4. 本轮明确不纳入白名单的候选文件：
   - `services/backtest/src/backtest/runner.py`
   - `services/backtest/src/backtest/strategy_base.py`
   - `services/backtest/tests/test_api_surface.py`
5. 验收标准：
   - 匹配 YAML 的正式回测不再以“Backtest execution failed: 回测结束”失败收口。
   - `agent-network` 能正确识别根级 `symbols:` 列表，不再误报 YAML 无 symbols。
   - 页面首屏不再出现 hydration mismatch。
6. 执行主体建议仍为：回测 Agent；本轮紧急执行口径以 Jay.S 当前会话授权 + 本节补充预审冻结范围为准。

## 十一、2026-04-05 终审结论（紧急补充范围 3 业务文件）

1. 本地自校验通过：`services/backtest/src/backtest/generic_strategy.py`、`services/backtest/backtest_web/app/agent-network/page.tsx`、`services/backtest/tests/test_generic_strategy_pipeline.py` 静态诊断为 0。
2. 回归测试要求冻结为：补充 `generic_strategy` 收尾异常回归用例，确保 `BacktestFinished` 在最终快照 / finish 阶段不会再把正式回测误收口为 failed。
3. 终审结论：通过，可以进入锁回。

## 十二、2026-04-06 单文件补充预审（日亏损限制百分比输入收口）

1. 补充预审成立，原因是当前需求仅落在 `services/backtest/backtest_web/app/agent-network/page.tsx` 单文件，且其本质仍属于 `TASK-0004` 的 backtest 看板前端交互收口，不构成 `TASK-0008` 的正式引擎泛化或正式报告导出任务。
2. 任务号结论冻结为：**继续归属 `TASK-0004`**。本次不得改挂 `TASK-0008`，因为 `TASK-0008` 当前冻结的是更大批次白名单与不同执行主体口径，若误复用将扩大风险半径。
3. 本轮最小业务文件白名单冻结为 1 个文件：`services/backtest/backtest_web/app/agent-network/page.tsx`。
4. 执行主体冻结为：**回测 Agent**。本轮不接受 Atlas 直修口径，也不接受扩展到第 2 个业务文件。
5. 变更语义冻结为：仅把“日亏损限制”前端输入 / 显示方式统一为与“最大回撤”一致的百分比口径；YAML 内部保存值仍必须保持 `0..1` 原始比例小数，不改变执行语义。
6. 本轮明确禁止扩展到：
   - `services/backtest/backtest_web/app/operations/page.tsx`
   - `services/backtest/backtest_web/app/page.tsx`
   - `services/backtest/backtest_web/src/**`
   - `services/backtest/src/**`
   - `shared/contracts/**`
7. 验收标准冻结为：
   - 输入 `0.7` 时，保存值必须为 `0.007`
   - 重新读取 `0.007` 时，显示值必须为 `0.7`
   - `maxDrawdown` 现有百分比交互不得回归
   - `positionFraction` 现有行为不得回归
8. 风险冻结为：不得顺手改摘要文案、后端解析、helper、operations 页面联动或其他风控字段；一旦执行中证明必须新增第 2 个业务文件，当前补充范围立即失效，必须回交补充预审。
9. 约束引用：`TASK-0008` 中“用户未来导入的策略不得变更任何一个数字或符号，必须按 YAML 原值执行”的冻结语义，本轮作为执行约束继续生效；但其任务号、白名单与执行主体不转移到本轮。
10. 当前执行口径可按“Jay.S 当前会话授权 + 本节单文件冻结范围”准备实施；按要求不在 review 中伪造 `token_id`。

## 十三、2026-04-06 单文件补充终审结论（日亏损限制百分比输入收口）

1. 终审取证来源已交叉核验：
   - `docs/reviews/TASK-0004-review.md` 与 `docs/locks/TASK-0004-lock.md` 的单文件补充预审范围一致，均冻结为 `services/backtest/backtest_web/app/agent-network/page.tsx`。
   - `docs/prompts/agents/回测提示词.md` 已记录本轮仅修改 `app/agent-network/page.tsx`，且未扩展到 `app/operations/page.tsx`、`src/**`、后端或 contract。
   - 本轮只读诊断结果确认：`services/backtest/backtest_web/app/agent-network/page.tsx` 与 `docs/prompts/agents/回测提示词.md` 均为 `No errors found`。
2. 单文件语义闭环核验通过：
   - 读取链路：`buildSystemConfigFromYaml()` 继续从 `risk.daily_loss_limit` / `risk.daily_loss_limit_yuan` 读取原始比例小数，未改为百分比持久化。
   - 输入链路：`dailyLossLimit` 已改为与 `maxDrawdown` 一致，使用 `formatPercentInput()` 展示、`parsePercentInput()` 回写。
   - 写出链路：`buildSystemRiskBlock()` 继续直接写出 `config.dailyLossLimit.trim()`，保持 YAML/state 的 `0..1` 比例小数语义。
   - 因此输入 `0.7` 时，`parsePercentInput()` 会写回 `0.007`；读取 `0.007` 时，`formatPercentInput()` 会显示 `0.7`；`formatDecimalAsPercent()` 同步展示当前保存值 `0.7%`，语义闭环成立。
3. 白名单边界核验通过：未发现本轮扩展到以下任一范围：
   - `services/backtest/backtest_web/app/operations/page.tsx`
   - `services/backtest/backtest_web/app/page.tsx`
   - `services/backtest/backtest_web/src/**`
   - `services/backtest/src/**`
   - `shared/contracts/**`
4. 回归约束核验通过：`maxDrawdown` 仍沿用既有百分比输入实现；`positionFraction` 现有百分比输入实现未被回退。
5. 终审结论：通过，无阻断项；本轮单文件补充已满足“只动 1 个业务文件、白名单未越界、输入/保存/读取语义闭环成立”的验收标准。
6. 锁回结论：可以锁回，并应立即恢复 `services/backtest/backtest_web/app/agent-network/page.tsx` 的锁定状态；后续如需再次修改该文件，必须重新补充预审与解锁。