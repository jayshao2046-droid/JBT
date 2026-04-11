# Atlas To Qwen Phase C Step 3

【签名】Atlas
【时间】2026-04-11
【设备】MacBook

## 1. 本轮目标

在 Step 1 的全量矩阵和 Step 2 的首批候选包基础上，把 **整个 Phase C** 整理成一份“可按天推进的全量部署/预审编排板”。

这里的“部署”指：

1. 哪些项应先建单
2. 哪些项应先预审
3. 哪些项可并行
4. 哪些项必须后置
5. 哪些项天然受 SG / 保护区 / 跨服务依赖限制

本轮仍然只读，不改代码。

## 2. 输入材料

1. `docs/handoffs/qwen-audit-collab/ATLAS_TO_QWEN_PHASE_C_STEP1.md`（当前 Step 1 权威矩阵）
2. `docs/handoffs/qwen-audit-collab/QWEN_PHASE_C_STEP2_REPORT.md`
3. `docs/handoffs/qwen-audit-collab/ATLAS_PHASE_C_STEP2_REVIEW.md`（若存在，必须吸收其中修正意见）
4. `docs/JBT_FINAL_MASTER_PLAN.md` 中完整 Phase C 定义
5. 必要时补读相关服务目录与 review / handoff / README

## 3. 硬约束

1. 不得发明新的正式 `TASK-XXXX` 编号。
2. 不得把建议队列直接写成“已获准实施”。
3. 必须覆盖完整 `C0 / CA / CB / CG / CF / CS / CK`，不能只写首批三项。
4. 对跨服务项，必须明确主责方与协同方，不得写模糊口径。
5. 对涉及 `shared/contracts/**`、`shared/python-common/**`、`.github/**`、`docker-compose.dev.yml`、任一 `.env.example` 的事项，必须明确标记为 `protected`。
6. 对当前仓内未见现成实现锚点的事项，必须明确写“计划定义已存在，但实现锚点不足”。
7. 必须保留当前总控事实：SG 仍在前置，不得把本轮输出写成“今天直接全量开写”。
8. 若 Step 2 已标记某事项为 `planned-placeholder`，Step 3 不得把它升级表述为“真实现成锚点已清楚”。
9. 若 `ATLAS_PHASE_C_STEP2_REVIEW.md` 存在，Step 3 必须吸收其中对 ready 状态、跨服务门禁和锚点类型的修正，不得继续沿用已被 Atlas 指出的错误口径。

## 4. 输出文件

请把结果写入：

`docs/handoffs/qwen-audit-collab/QWEN_PHASE_C_STEP3_REPORT.md`

## 5. 输出结构

请严格使用以下结构：

1. Step 3 执行摘要
2. 全量推进编排板
   - `Lane-A`：可优先建单候选
   - `Lane-B`：需先完成前置依赖后再建单
   - `Lane-C`：跨服务 / 受保护区 / 高风险后置项
3. Phase C 全量优先级表
   - 每项至少给出：编号、主责、依赖、当前状态、建议时机
4. 并行关系图（文字即可）
5. 当天最合理推进顺序
   - 第 1 手
   - 第 2 手
   - 第 3 手
   - 第 4 手以后
6. 不建议今天硬推的事项
7. 给 Atlas 的最终派发建议
8. 给 Jay.S 的一句话摘要

## 6. 额外要求

1. `Lane-A` 不要求已经拿到授权，但必须达到“事实清楚，适合交项目架构师预审”的程度。
2. `Lane-B` 必须写清前置缺口是什么，而不是只写“后置”。
3. `Lane-C` 必须说明是因为跨服务、受保护区、架构复杂度，还是依赖不存在。
4. 你必须显式说明以下关系如何落地到编排顺序：
   - `C0-1 ⊥ C0-3 -> C0-2`
   - `CA2' ⊥ CB2'`
   - `CA/CB -> CG`
   - `CK1 -> CK2 -> CK3`
   - `CS1/CS1-S` 与双沙箱的关系

## 7. Atlas 当前用途说明

这份 Step 3 回执会被 Atlas 用于：

1. 把整个 Phase C 从“总计划定义”推进到“分日执行队列”
2. 判断今天最多能把哪些项推进到待预审 / 待签发
3. 作为后续给项目架构师和 Jay.S 的压缩版执行排序底稿