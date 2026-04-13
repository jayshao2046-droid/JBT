# Claude Code 派发单 Phase 2 — TASK-0079-N + TASK-0080

【签名】Atlas  
【时间】2026-04-13  
【设备】MacBook  
【状态】⏳ 待执行（前置：TASK-0077/0078/0079 Atlas 审核通过 + Studio 容器重建完成）

---

## 执行协议

1. TASK-0079-N（Navbar）可在 TASK-0077/0078/0079 与 TASK-0079-N 合并到同一次派发
2. TASK-0080（G0 工作区切割）必须等 Studio 容器重建完成后再执行
3. 每个任务单独 commit

---

## TASK-0079-N — Navbar 导航补充

**Token ID:** `tok-60c4ba0a`  
**白名单:** 1 文件 — `services/decision/decision_web/components/Navbar.tsx`  

### 当前 Navbar.tsx 状态

```typescript
const navItems = [
  { href: "/", label: "首页" },
  { href: "/research", label: "策略研究" },
]
```

### 需要修改为

```typescript
const navItems = [
  { href: "/", label: "首页" },
  { href: "/research", label: "策略研究" },
  { href: "/import", label: "策略导入" },
  { href: "/optimizer", label: "参数调优" },
  { href: "/reports", label: "回测报告" },
]
```

只需要这一处修改，其余 Navbar 代码保持不变。

### commit 格式
```
feat(decision-web): TASK-0079-N Navbar添加导入/调优/报告导航入口
```

---

## TASK-0080 — G0 工作区切割

**Token ID:** `tok-b7a463ce`  
**白名单:** 1 文件 — `JBT-Control.code-workspace`  

### 当前文件内容

```json
{
  "folders": [
    {
      "name": "JBT",
      "path": "."
    },
    {
      "name": "J_BotQuant_legacy",
      "path": "/Users/jayshao/J_BotQuant"
    }
  ],
  ...
}
```

### 修改为（删除 J_BotQuant_legacy 条目）

```json
{
  "folders": [
    {
      "name": "JBT",
      "path": "."
    }
  ],
  ...
}
```

保留 `settings` 块不变，只删除 `J_BotQuant_legacy` folder 条目。

### commit 格式
```
chore(governance): TASK-0080 G0 J_BotQuant工作区切割
```

---

## 执行完成后

汇报：
1. TASK-0079-N commit hash
2. TASK-0080 commit hash
