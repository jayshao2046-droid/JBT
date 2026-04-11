# Atlas To Qwen Phase C Step 2

【签名】Atlas
【时间】2026-04-11
【设备】MacBook

## 1. 本轮目标

在 Step 1 的全量拆批矩阵基础上，把 **首批最适合先推进的候选项** 收敛成“可直接交 Atlas 复核、再转项目架构师预审”的候选预审包。

本轮仍然只读，不改代码，不写正式任务号。

## 2. 本轮冻结对象

除非你在 Step 1 中发现明确反证，否则本轮默认固定收敛以下 3 个候选项：

1. `C0-1` 股票 bars API 路由扩展
2. `CB5` 动态 watchlist 分钟 K 采集
3. `CG2` 人工手动回测 + 审核确认

如果你认为其中某一项必须替换，必须满足两条：

1. 给出真实仓库证据说明它不适合作为第一批
2. 明确写出替代项为何更小、更快、更适合先手

## 3. 必读输入

1. `docs/handoffs/qwen-audit-collab/ATLAS_TO_QWEN_PHASE_C_STEP1.md`（当前 Step 1 的权威矩阵，以此为准）
2. 若你另存了 `docs/handoffs/qwen-audit-collab/QWEN_PHASE_C_STEP1_REPORT.md`，可作为补充；若该文件不存在，不得因此停摆，直接以上述 Step 1 矩阵文件继续推进
3. `docs/JBT_FINAL_MASTER_PLAN.md` 的 Phase C 段落
4. 相关服务真实文件：
   - `services/data/**`
   - `services/decision/**`
   - `services/backtest/**`

## 4. 硬约束

1. 全程只读，不修改任何业务代码、契约、治理文件或 prompt。
2. 不得发明新的正式 `TASK-XXXX` 编号。
3. 不得把建议文件范围写成“已冻结白名单”或“已批准修改范围”。
4. 若涉及跨服务、受保护区、共享契约、共享库、部署文件，必须显式标记：`需项目架构师预审 + Token`。
5. 每个候选项都必须收敛到最小必要范围，不得顺手把“未来可能要动”的文件一并塞入。
6. 若某候选项仍然缺关键锚点或依赖未清，必须明确标记为 `not ready for pre-review`。
7. 不得绕过 SG 当前顺序，把本轮候选包写成“可立即开发”；本轮只是给 Atlas 准备更快的预审入口。
8. 对 Step 1 中当前仓内不存在的路径，不得继续写成“真实已存在锚点”；必须区分 `existing-anchor` 与 `planned-placeholder`。

## 5. 输出文件

请把结果写入：

`docs/handoffs/qwen-audit-collab/QWEN_PHASE_C_STEP2_REPORT.md`

## 6. 输出结构

请严格使用以下结构：

1. Step 2 执行摘要
2. 候选项 A：`C0-1`
3. 候选项 B：`CB5`
4. 候选项 C：`CG2`
5. 三项并行 / 串行关系
6. 给 Atlas 的预审建议顺序
7. 给 Jay.S 的一句话摘要

## 7. 每个候选项必须包含的字段

每个候选项至少包含：

1. 候选项编号与名称
2. 当前是否具备进入预审条件：
   - `ready-for-pre-review`
   - `needs-more-readonly-proof`
   - `blocked`
3. 主责服务 / 协同服务
4. 真实仓库锚点
5. 建议最小业务文件范围（只是建议，不是白名单）
6. 依赖项
7. 最小验证方式
8. 主要风险
9. 是否触及受保护区域
10. 锚点类型：`existing-anchor` / `planned-placeholder`
11. Atlas 若要建单，最适合拆成几批

## 8. Atlas 当前用途说明

这份 Step 2 回执会被 Atlas 用于：

1. 快速判断三项里哪一项可以先交项目架构师预审
2. 决定当天第一批实际要先推哪一个服务
3. 如果 Step 1 有瑕疵，也能先基于 Step 2 的收敛结果继续推进，不至于停摆