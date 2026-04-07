# TASK-0021 Review

## Review 信息

- 任务 ID：TASK-0021
- 审核角色：项目架构师
- 审核阶段：总包执行治理准备终审同步
- 审核时间：2026-04-07
- 审核结论：通过（当前正式状态已从“仅批次 A 冻结待签”升级为“总包执行治理已就绪”；执行组织固定为“项目架构师 + 决策 agent”，不使用 Livis；A 批 contracts 10 文件 Token 已 active，可直接开工；其余批次待 Jay.S 按 Manifest 一次性签发）

---

## 一、当前固定口径

1. `TASK-0021` 继续独立成立，不并入 `TASK-0016` 或 `TASK-0012`，三者不得复用白名单、Token、验收或回滚口径。
2. 当前执行组织固定为：**项目架构师 + 决策 agent**。
3. 当前明确不使用 Livis；本线不切换为 Livis 协作模式。
4. 当前允许直接进入的代码范围仅为批次 A 对应的 `shared/contracts/**` 10 文件正式范围。

## 二、本轮治理补充同步文件

1. `docs/reviews/TASK-0021-review.md`
2. `docs/locks/TASK-0021-lock.md`
3. `docs/handoffs/TASK-0021-总包执行与Token清单.md`
4. `docs/prompts/公共项目提示词.md`
5. `docs/prompts/agents/项目架构师提示词.md`

说明：本轮仅补充 P-LOG 治理留痕，不触碰 `services/**`、`shared/contracts/**`、`integrations/**` 或 legacy 代码目录本身。

## 三、当前 Token 状态判定

1. **批次 A：已 active，可直接开工。**
2. 批次 A 当前正式范围固定为 10 文件：
	- `shared/contracts/README.md`
	- `shared/contracts/decision/api.md`
	- `shared/contracts/decision/strategy_package.md`
	- `shared/contracts/decision/research_snapshot.md`
	- `shared/contracts/decision/backtest_certificate.md`
	- `shared/contracts/decision/decision_request.md`
	- `shared/contracts/decision/decision_result.md`
	- `shared/contracts/decision/model_boundary.md`
	- `shared/contracts/decision/notification_event.md`
	- `shared/contracts/decision/dashboard_projection.md`
3. **批次 B、C0、C、D、E0、E、F0、F、G 当前均未 active。**
4. 其余批次当前状态统一冻结为：**待 Jay.S 按 `docs/handoffs/TASK-0021-总包执行与Token清单.md` 一次性签发，不得提前越权执行。**

## 四、总包批次冻结清单

| 批次 | 范围 | 保护级别 | 执行主体 | 是否必须先补 Token | 主要产物 |
|---|---|---|---|---|---|
| A | `shared/contracts/README.md` + `shared/contracts/decision/*.md` 正式契约 | P0 | 决策 agent | 否，当前已 active | decision 正式契约索引、请求/结果模型、策略包元数据、研究快照、回测证明、模型边界、通知事件、看板只读聚合字段 |
| B | `integrations/legacy-botquant/**` 决策迁移期只读适配层 | P0 | 决策 agent | 是 | legacy 决策输入映射、只读兼容适配、迁移期边界封装 |
| C0 | `services/decision/.env.example` 及决策服务受保护模板配置 | P0 | 决策 agent | 是 | 决策服务环境模板、模型路由占位、研究窗口与发布门禁占位 |
| C | `services/decision/src/**`、`services/decision/tests/**`、必要 `configs/**` | P1 | 决策 agent | 是 | 决策 API、审批编排、策略仓库、模型路由、执行资格门禁 |
| D | `services/decision/src/research/**`、`services/decision/src/gating/**`、对应测试 | P1 | 决策 agent | 是 | 研究中心主线、XGBoost 研究编排、因子/回测/研究联动门禁 |
| E0 | `services/dashboard/.env.example` 及决策看板受保护模板配置 | P0 | 决策 agent | 是 | 决策看板环境模板、只读聚合入口与开关占位 |
| E | `services/dashboard/**` 决策看板实现范围 | P1 | 决策 agent | 是 | 7 页决策看板、策略仓库前台、模型与因子页、通知与日报页 |
| F0 | `docker-compose.dev.yml`、`services/decision/Dockerfile`、`services/dashboard/Dockerfile`、`deploy/**`、反代/部署文件 | P0 | 决策 agent（项目架构师先预审） | 是 | 决策/看板部署骨架、容器化、反代与发布配置 |
| F | `services/decision/src/notifier/**`、`services/decision/src/reporting/**`、对应测试 | P1 | 决策 agent | 是 | 飞书/邮件通知链路、研究完成摘要、日报周报月报 |
| G | `services/decision/src/publish/**`、相关 API/测试、收口交接所需治理留痕 | P1 | 决策 agent | 是 | 仅推送到 `sim-trading` 的发布链路、`live-trading` 锁定可见入口、迁移收口与验收交接 |

## 五、关键风险与约束

1. 批次 A 已 active，不等于 B~G 可提前执行；除 A 外其余批次继续锁定。
2. `C0`、`E0`、`F0` 必须保持独立 P0，不得混入对应 P1 实施批次。
3. `F0` 涉及 `.env.example`、compose、Dockerfile、deploy/反代配置，必须单独受控，不得与业务实现混提交流水。
4. `G` 仅允许构建“发布到模拟交易、实盘入口锁定可见”的链路；不得借此扩写 `services/sim-trading/**` 或 `services/live-trading/**`。
5. 在 Jay.S 完成 Manifest 签发前，批次 B~G 全部视为未解锁。

## 六、终审结论

1. **`TASK-0021` 已完成“总包执行治理准备”同步。**
2. **执行组织正式冻结为“项目架构师 + 决策 agent”，且明确不使用 Livis。**
3. **当前 A 批 contracts 10 文件 Token 已 active，可直接开工。**
4. **总包批次清单已冻结为 A、B、C0、C、D、E0、E、F0、F、G。**
5. **当前下一动作已冻结为：先执行 A 批 contracts；随后由 Jay.S 按 Manifest 一次性签发后续批次。**