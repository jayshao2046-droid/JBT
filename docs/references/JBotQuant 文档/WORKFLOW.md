# BotQuant Development Workflow — v7.0

**版本：** v7.0.0
**更新日期：** 2026-03-17
**状态：** Active

=============================================================
## 1. 核心原则
=============================================================

- **单一事实来源：** 所有计划、代码和文档均以 `main` 分支为唯一基准。
- **责任分离：** Atlas (PM) / Livis (Arch) / 子 Agent (Dev) 严格分工。
- **确认驱动：** 任何关键操作都必须得到 Jay.S 的明确批准。
- **自动化优先：** 测试、审查、部署、备份尽可能自动化。

=============================================================
## 2. 九步协作工作流
=============================================================

```
Jay.S 需求 → ① Atlas 拆解任务 → ② Jay.S 审批
                                        ↓
                              ③ Atlas 派发给 Livis
                                        ↓
                              ④ Livis 技术分解 → 分配子 Agent
                                        ↓
                              ⑤ 子 Agent 开发 + 自测
                                        ↓
                              ⑥ Livis 代码审查
                                        ↓
                              ⑦ Livis 提交 + 三地同步
                                        ↓
                              ⑧ Atlas 最终验收
                                        ↓
                              ⑨ Atlas 更新进度
```

### 步骤详解

**① Atlas 拆解任务**
- 输入: Jay.S 需求 + `PROJECT_MASTER_PLAN.md`
- 输出: 状态为 "⏳ 待确认" 的任务派发单

**② Jay.S 审批**
- 审查任务合理性、验收标准和优先级
- 输出: "确认" 或修改意见

**③ Atlas 派发**
- 确认后正式派发给 Livis
- 更新状态为 "🚀 进行中"

**④ Livis 技术分解**
- 进行技术方案设计，分配给最合适的子 Agent

**⑤ 子 Agent 开发**
- 编写代码、单元测试和相关文档

**⑥ Livis 审查**
- 审查代码质量、风格和实现逻辑
- 输出: "通过" 或 "驳回修改"

**⑦ Livis 提交同步**
1. `git commit -m "feat(TXXX): 任务描述"`
2. `git push origin main`
3. `ssh mini "cd ~/J_BotQuant && git pull"`
4. `ssh studio "cd ~/J_BotQuant && git pull"`

**⑧ Atlas 验收**
- 验收三要素: Git Commit + 三地同步 + 功能/文档
- 输出: 任务验收单

**⑨ Atlas 更新进度**
- 更新 `ATLAS_MASTER_PLAN.md` 任务状态和总体进度

=============================================================
## 3. 每日工作流程
=============================================================

**工作前：**
1. 读取 `PROJECT_CONTEXT.md` 了解最新状态
2. Atlas 拆解当日任务
3. 确认网络环境：内网 / 外网

**工作中：**
1. 按 Plan 步骤逐一执行
2. 每步完成后暂停等确认
3. 遇到问题立即停顿沟通

**工作后：**
1. 更新 `LIVIS_PROMPT.md` 工作记录
2. Git 提交并同步三地
3. Atlas 更新 `Atlas_prompt.md`
4. 更新 `PROJECT_CONTEXT.md`

=============================================================
## 4. Git 规范
=============================================================

### 提交格式
```
<type>(<scope>): <subject>
```
- **type:** feat / fix / docs / style / refactor / test / chore
- **scope:** 任务 ID (如 T102) 或模块名
- **示例:** `feat(T102): Implement Dockerfile for data service`

### 分支规则
- `main` 分支为主分支
- 排除文件: `.env` 切勿提交
- 提交频率: 每完成一个子任务提交一次

### 三地同步
```bash
# 推送后自动触发
ssh mini "cd ~/J_BotQuant && git pull origin main"
ssh studio "cd ~/J_BotQuant && git pull origin main"
# 验证同步
python3 scripts/governance/sync_verify.py
```

=============================================================
## 5. 备份规范
=============================================================

| 类型 | 保留策略 | 位置 |
|---|---|---|
| 代码 | Git + 最近 4 次快照 | `~/J_BQ_backup/` |
| 数据 | NAS 永久 + 本地 7 天 | `~/J_BotQuant/BotQuan_Data/` |
| 日志 | NAS 永久 + 本地 30 天 | `~/J_BotQuant/logs/` |
| NAS 备份 | 每日 03:00-05:00 | `/Volumes/docker/J_BotQuant/` |

备份验证: `nas_backup.sh` 含文件计数 + 哈希抽样校验

=============================================================
## 6. 角色分工
=============================================================

| 角色 | 职责 | 不可做 |
|---|---|---|
| **Jay.S** | 方向确认、方案审批、最终验收 | — |
| **Atlas** | 进度管理、任务拆解、质量验收 | 不可写代码、不可做技术决策 |
| **Livis** | 代码审查、技术决策、子 Agent 协调 | 不可跳过 Atlas 的验收流程 |
| **子 Agent** | 领域开发、单元测试 | 不可跳过 Livis 的审查 |

=============================================================
## 7. Agent Prompt 维护
=============================================================

| Prompt | 维护者 | 更新时机 |
|---|---|---|
| `Atlas_prompt.md` | Atlas | 每日结束或任务完成时 |
| `LIVIS_PROMPT.md` | Livis | 每任务完成后 |
| `PROJECT_CONTEXT.md` | Atlas | 每任务完成后 |
| `configs/agents/*.md` | 对应子 Agent | 职责变化时 |

=============================================================
## 8. 应急处理
=============================================================

**分钟采集中断：**
```bash
python3 ~/J_BotQuant/scripts/fetch_minute_kline_unified.py --phase day_am --symbols rb,hc,i,m,c,cf,y,p,oi,ta,ma,pp,v,ru
```

**看板无法访问：**
```bash
pkill -f streamlit && streamlit run src/dashboard/app.py --server.address=0.0.0.0 --server.port=8501
```

**蒲公英断开：** 重新登录蒲公英 APP

**调度器异常：**
```bash
ps aux | grep data_scheduler | grep -v grep
pkill -f data_scheduler
python3 ~/J_BotQuant/scripts/data_scheduler.py
```
