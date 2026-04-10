# TASK-0046 预审记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0046 |
| 任务标题 | RooCode 接入 JBT 业务流程与 Token 锁控预审 |
| 审核人 | 项目架构师（Atlas 代记录） |
| 审核日期 | 2026-04-11 |
| 审核结果 | ✅ 预审通过 |

---

## 编号修正说明

- 原 TASK-0044 / TASK-0045 中的 RooCode 接入事项统一改号为 TASK-0046。
- TASK-0045 已被 DR3"Mini macOS 容器自愈守护基线"正式占用。

---

## 预审检查清单

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 问题归属明确 | ✅ | 仓库级治理接入，不归属任何单服务 |
| 2 | 是否跨服务 / P0 | ✅ | 不触及 services/**、shared/contracts/**、.github/** |
| 3 | 现有治理工具复用 | ✅ | 复用 governance/jbt_lockctl.py，不改写 |
| 4 | 白名单最小必要 | ✅ | A1 冻结 5 项：ATLAS_PROMPT.md / .roomodes / .roo/mcp.json / .roo/rules/** / governance/roo_jbt_mcp_server.py |
| 5 | 业务 prompt 不分叉 | ✅ | 不新增 Roo 专用业务 prompt |
| 6 | 两条协作流程已冻结 | ✅ | 实施类 + 只读巡检类，共用 JBT 标准 task/review/lock/handoff/prompt |

---

## 预审意见

1. Roo 接入不构成第二套协作制度；所有留痕、Token、终审、lockback 继续走现有 JBT 标准流程。
2. `ATLAS_PROMPT.md` 仅作为 Roo 批次回写入口（署名 Roo），不得改写 Atlas 既有调度主体。
3. A1 白名单外的任何文件写入必须先补充预审。
4. `governance/jbt_lockctl.py` 仅复用不改写。

---

## 白名单冻结

### A0 批次（治理账本，无需 Token）

```
docs/tasks/TASK-0046-RooCode接入JBT业务流程与Token锁控预审.md
docs/reviews/TASK-0046-review.md
docs/locks/TASK-0046-lock.md
docs/handoffs/TASK-0046-架构预审交接单.md
```

### A1 批次（已终审通过并锁回）

```
ATLAS_PROMPT.md
.roomodes
.roo/mcp.json
.roo/rules/**
governance/roo_jbt_mcp_server.py
```

### A2 批次（已终审通过并锁回）

```
.gitignore
```

- Token：tok-1f28c19b-b4dd-461a-8f50-c01de9ecac64
- Review-ID：REVIEW-TASK-0046-A2
- 审核结果：✅ 终审通过
- 说明：仅移除 `.gitignore` 中 `.roo/` 排除规则，使 `.roo/mcp.json` 和 `.roo/rules/01-jbt-governance.md` 纳入版本控制

---

【签名】Atlas（代项目架构师记录）
【时间】2026-04-11
【设备】MacBook
