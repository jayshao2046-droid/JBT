# TASK-0049 预审记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0049 |
| 任务标题 | 全项目安全检查纳入总计划与统一修复预审 |
| 审核人 | 项目架构师 |
| 审核日期 | 2026-04-11 |
| 审核结果 | ✅ 预审通过，允许进入 A0 建档与 A1 计划同步准备 |

---

## 预审检查清单

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 问题归属明确 | ✅ | 本次为仓库级治理，不是单服务代码实施 |
| 2 | 策略端边界明确 | ✅ | 本轮“策略端”冻结为 `decision + backtest` |
| 3 | 顺序口径明确 | ✅ | 先策略端安全检查，再策略端复核，再全域检查，最后统一修复 |
| 4 | 只读口径明确 | ✅ | 当前阶段不做即时修复，只冻结检查与复核顺序 |
| 5 | Token 口径明确 | ✅ | `docs/JBT_FINAL_MASTER_PLAN.md` 与 `ATLAS_PROMPT.md` 后续仍需最小文件级 Token |
| 6 | 保护区冲突已识别 | ✅ | `shared/contracts/**`、`shared/python-common/**`、部署文件、真实 `.env` 均不得纳入当前直接实施范围 |
| 7 | Phase 冲突已识别 | ✅ | 安全专项应写成横向治理线，不改写现有 Phase C 功能拆分 |
| 8 | RooCode 边界明确 | ✅ | 当前 Qwen 审计文件只构成只读证据，不构成代码白名单 |

---

## 预审意见

1. 建议新建 `TASK-0049`，不并入已闭环的 `TASK-0048`。
2. 总计划中不应直接新增“立即修复安全问题”的执行口径，而应新增“安全治理横线”，只冻结顺序与后续统一修复原则。
3. 当前策略侧已确认问题先落 `backtest` 的 `F-001`；`decision` 作为策略侧补充复核范围写入，但不得伪造出当前已确认的 decision 主问题。
4. data 侧 `F-002`、`F-003` 当前只能作为后续只读可达性复核事项写入总计划，不能误写成已批准代码修复。
5. `backtest` 当前继续保持维护观察，只允许参与策略侧只读安全检查与复核规划，不恢复常规功能开发。
6. 若后续统一修复触及受保护区域，必须另起独立预审与 Token，不得在本任务下顺带实施。

---

## 白名单冻结

### A0 批次（治理建档，无需 Token）

1. `docs/tasks/TASK-0049-全项目安全检查纳入总计划与统一修复预审.md`
2. `docs/reviews/TASK-0049-review.md`
3. `docs/locks/TASK-0049-lock.md`
4. `docs/handoffs/TASK-0049-架构预审交接单.md`

### A1 批次（已签发并 validate）

1. `docs/JBT_FINAL_MASTER_PLAN.md`
2. `ATLAS_PROMPT.md`

### A2 批次（P-LOG 同步，Atlas 侧已完成）

1. `docs/prompts/总项目经理调度提示词.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/总项目经理提示词.md`
4. `docs/prompts/agents/项目架构师提示词.md`

---

## 当前结论

1. `TASK-0049` 已完成 A0 建档准备。
2. 当前允许进入 A1 最小 Token 申请准备，但在 Jay.S 签发前不得修改 `docs/JBT_FINAL_MASTER_PLAN.md` 与 `ATLAS_PROMPT.md`。
3. 本轮正式治理结论为：先完成策略端安全检查，再完成策略端复核，再完成全域安全检查，最后统一进入修复预审与实施；当前阶段不做即时修复。

---

## 后续执行更新 [2026-04-11]

1. Jay.S 已为 A1 最小白名单签发 Token `tok-da51ff91-10d9-47f1-95ef-1d369f39fb1f`，并已 validate 通过，范围仍严格限于 `docs/JBT_FINAL_MASTER_PLAN.md` 与 `ATLAS_PROMPT.md`。
2. Atlas 已完成 A1 计划同步，`docs/JBT_FINAL_MASTER_PLAN.md` 已正式纳入 `SG1`~`SG5` 安全治理横线，且明确当前阶段不进入即时修复。
3. A2 当前仅允许 Atlas 完成其自有 prompt 同步；`docs/prompts/公共项目提示词.md` 与 `docs/prompts/agents/项目架构师提示词.md` 继续保留给项目架构师按角色补齐。

---

【签名】项目架构师
【时间】2026-04-11
【设备】MacBook