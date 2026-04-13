# TASK-0092 — Decision 看板全面增强 第三阶段（P3）

**任务编号**：TASK-0092  
**创建时间**：2026-04-13  
**创建人**：Atlas  
**执行人**：Claude Code  
**状态**：🔓 待执行（与 TASK-0090 同批授权）

---

## 一、功能范围（P3，3项）

| 编号 | 功能 |
|------|------|
| P3-1 | 键盘快捷键系统（8个全局快捷键） |
| P3-2 | 主题切换（暗色/亮色 + 持久化） |
| P3-3 | 决策热力图（参数热力图 + 月度信号分布） |

---

## 二、文件白名单（5个文件）

| 操作 | 文件路径 |
|------|---------|
| 新建 | `services/decision/decision_web/components/DecisionHeatmap.tsx` |
| 新建 | `services/decision/decision_web/components/ThemeToggle.tsx` |
| 新建 | `services/decision/decision_web/components/KeyboardShortcutsHelp.tsx` |
| 新建 | `services/decision/decision_web/lib/keyboard.ts` |
| 修改 | `services/decision/decision_web/app/decisions/page.tsx` |

**总计：5 文件（全部前端）**

---

## 三、边界约束

1. 严格限于 `services/decision/**`
2. Tailwind dark 模式，无需新依赖
