# TASK-0089 — Backtest 看板全面增强 第三阶段（P3）

**任务编号**：TASK-0089  
**参考**：BACKTEST-WEB-03（Claude 申请）  
**创建时间**：2026-04-13  
**创建人**：Atlas  
**执行人**：Claude Code  
**状态**：🔒 已完成  
**前置**：TASK-0088 完成验收后方可执行

---

## 一、功能范围（P3，3项）

| 编号 | 功能 | 说明 |
|------|------|------|
| P3-1 | 键盘快捷键系统 | 8个全局快捷键 + 快捷键帮助面板 |
| P3-2 | 主题切换 | 暗色/亮色模式 + localStorage 持久化 |
| P3-3 | 回测热力图 | 参数热力图（参数组合 vs 收益率）+ 月度收益分布 |

---

## 二、文件白名单（5个文件）

### 前端（TypeScript/React）

| 操作 | 文件路径 |
|------|---------|
| 新建 | `services/backtest/backtest_web/components/BacktestHeatmap.tsx` |
| 新建 | `services/backtest/backtest_web/components/ThemeToggle.tsx` |
| 新建 | `services/backtest/backtest_web/components/KeyboardShortcutsHelp.tsx` |
| 新建 | `services/backtest/backtest_web/lib/keyboard.ts` |
| 修改 | `services/backtest/backtest_web/app/backtest/page.tsx` |

**总计：5 文件（全部前端）**

---

## 三、边界约束

1. 严格限于 `services/backtest/**`，禁止跨服务
2. 主题切换使用 Tailwind CSS dark 模式，无需额外依赖
3. 不修改 `docker-compose.dev.yml`、`.env.example`、`shared/**`

---

## 四、验收标准

- [x] `pnpm build` Compiled successfully，无 TypeScript 错误
- [x] P3-1：键盘快捷键系统正常工作（8个快捷键）
- [x] P3-2：主题切换功能正常（暗色/亮色，持久化）
- [x] P3-3：参数热力图和月度收益分布显示正常

---

## 五、关联文档

- 父任务：[TASK-0088](./TASK-0088-backtest-看板增强-P2阶段.md)
- 预审：[TASK-0089-review.md](../reviews/TASK-0089-review.md)
- Token 申请：[BACKTEST-WEB-Token申请-Claude.md](../handoffs/BACKTEST-WEB-Token申请-Claude.md)
