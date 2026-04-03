# TASK-0004 Review

## Review 信息

- 任务 ID：TASK-0004
- 审核角色：项目架构师
- 审核阶段：看板阶段预审
- 审核时间：2026-04-03
- 审核结论：通过（范围冻结为 `services/backtest/V0-backtext 看板/` 内两页收敛；当前最小业务白名单仅 3 文件；`app/layout.tsx`、`package.json` 与其余页面不纳入本轮；默认以停用导航 / 停止引用替代删除；当前可进入 Jay.S Token 签发准备态）

---

## 一、任务边界核验

1. 任务目标明确：将现有 backtest 看板原型收敛为“策略管理 + 回测详情”两类页面。
2. 任务目录明确：仅限 `services/backtest/V0-backtext 看板/`。
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

1. `services/backtest/V0-backtext 看板/app/page.tsx`
2. `services/backtest/V0-backtext 看板/app/agent-network/page.tsx`
3. `services/backtest/V0-backtext 看板/app/operations/page.tsx`

### 当前不建议纳入的文件

1. `services/backtest/V0-backtext 看板/app/layout.tsx`
2. `services/backtest/V0-backtext 看板/package.json`
3. `services/backtest/V0-backtext 看板/app/command-center/page.tsx`
4. `services/backtest/V0-backtext 看板/app/intelligence/page.tsx`
5. `services/backtest/V0-backtext 看板/app/systems/page.tsx`

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
3. **建议签发单 Agent、单任务、3 文件的 P1 Token。**
4. **当前公共状态应切换为“TASK-0004 看板阶段已预审，待 Jay.S 签发 Token”。**