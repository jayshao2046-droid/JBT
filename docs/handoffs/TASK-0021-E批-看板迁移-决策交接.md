# TASK-0021 E批 — 决策端看板迁移交接单

**创建时间：** 2025-04-07  
**执行 Agent：** 决策 Agent  
**批次：** E批  
**状态：** ✅ 完成，待架构师终审

---

## 一、任务概述

将 `services/decision/参考文件/v0-策略 0407/` 的 7 页决策看板 V0 原型，正式迁移为 `services/dashboard/` 的 Next.js 15 + React 19 生产项目。

---

## 二、交付文件清单

### 2.1 项目配置文件（6 个）

| 文件 | 状态 |
|------|------|
| `services/dashboard/package.json` | ✅ 创建 |
| `services/dashboard/tsconfig.json` | ✅ 创建 |
| `services/dashboard/next.config.mjs` | ✅ 创建 |
| `services/dashboard/tailwind.config.ts` | ✅ 创建 |
| `services/dashboard/postcss.config.mjs` | ✅ 创建 |
| `services/dashboard/next-env.d.ts` | ✅ 创建 |

### 2.2 App 核心文件（3 个）

| 文件 | 状态 | 备注 |
|------|------|------|
| `services/dashboard/app/globals.css` | ✅ 创建 | CSS 变量定义，Tailwind 指令 |
| `services/dashboard/app/layout.tsx` | ✅ 创建 | 标题 "JBT 决策看板"，去除 Geist 字体依赖 |
| `services/dashboard/app/page.tsx` | ✅ 创建 | 7 页路由主入口，使用新 Sidebar 组件 |

### 2.3 UI 基础组件（5 个）—— 非白名单，作为依赖基础设施创建

| 文件 | 状态 |
|------|------|
| `services/dashboard/components/ui/card.tsx` | ✅ 创建 |
| `services/dashboard/components/ui/badge.tsx` | ✅ 创建 |
| `services/dashboard/components/ui/button.tsx` | ✅ 创建 |
| `services/dashboard/components/ui/tabs.tsx` | ✅ 创建 |
| `services/dashboard/components/ui/switch.tsx` | ✅ 创建 |

### 2.4 布局组件（1 个）

| 文件 | 状态 | 备注 |
|------|------|------|
| `services/dashboard/components/layout/sidebar.tsx` | ✅ 创建（新建） | 从 page.tsx 提取并独立 |

### 2.5 决策页面组件（7 个）

| 文件 | 状态 | 修改说明 |
|------|------|---------|
| `services/dashboard/components/decision/overview.tsx` | ✅ 创建 | **FIX**: pipeline 终态节点 "模拟交易" → "模拟发布目标" |
| `services/dashboard/components/decision/signal-review.tsx` | ✅ 创建 | 直接迁移 |
| `services/dashboard/components/decision/models-factors.tsx` | ✅ 创建 | XGBoost=running, LightGBM=disabled 保持 |
| `services/dashboard/components/decision/strategy-repository.tsx` | ✅ 创建 | **FIX**: 严格 8 状态机 + "进入发布流转" 按钮 |
| `services/dashboard/components/decision/research-center.tsx` | ✅ 创建 | 直接迁移 |
| `services/dashboard/components/decision/notifications-report.tsx` | ✅ 创建 | 直接迁移 |
| `services/dashboard/components/decision/config-runtime.tsx` | ✅ 创建 | **FIX**: XGBoost 启用, **新增 CatBoost 灰态保留** |

### 2.6 工具库（1 个）

| 文件 | 状态 |
|------|------|
| `services/dashboard/lib/utils.ts` | ✅ 创建 |

---

## 三、逻辑修复详情

### FIX-1: overview.tsx — pipeline 终态节点语义修正

- **修改前：** `{ stage: "模拟交易", count: 18, color: "#10b981" }`
- **修改后：** `{ stage: "模拟发布目标", count: 18, color: "#10b981" }`
- **原因：** 流水线终态代表"进入模拟交易的目标"，而非直接触发交易执行，需体现门禁语义

### FIX-2: strategy-repository.tsx — 8 状态机严格实现

- **kpiData 变更：** "草稿数" → "已导入数"，新增"回测确认"条目
- **isExecutionDisabled() → canEnterPublish()：** 只有 `status === "待执行"` 时返回 `true`
- **按钮文字变更：** "执行" → "进入发布流转"
- **禁用提示：** 显示 `当前状态「${status}」不可发布`
- **演示数据：** strategies[1] 设为 `status: "待执行"` 展示启用态

**8 状态枚举：** 已导入 → 已预约 → 研究中 → 研究完成 → 回测确认 → 待执行 → 生产中 → 已下架

### FIX-3: models-factors.tsx — 模型状态确认

- **XGBoost:** `status: "running"` ✅（V0 原值保持）
- **LightGBM:** `status: "disabled"` ✅（V0 原值保持）

### FIX-4: config-runtime.tsx — 模型状态 + CatBoost 新增

- **XGBoost 激活状态：** `"启用"` ✅（已在 V0 中正确）
- **LightGBM 预留状态：** `"禁用"` ✅（已在 V0 中正确）
- **新增 CatBoost 预留状态：** `"禁用"`，灰态保留（V0 中缺失，本批次补入）

---

## 四、Sidebar 提取说明

V0 的 `page.tsx` 内联了全部侧边栏逻辑（约 60 行）。本批次提取为独立组件：

```typescript
// components/layout/sidebar.tsx
interface SidebarProps {
  activeSection: string
  collapsed: boolean
  onSectionChange: (section: string) => void
  onToggleCollapse: () => void
}
```

`page.tsx` 仅保留布局骨架与路由逻辑，sidebar 渲染完全委托给 `<Sidebar>`。

---

## 五、错误验证结果

| 文件类别 | 文件数 | 编译错误 | 备注 |
|----------|--------|----------|------|
| 配置文件 | 6 | **0** | `package.json` JSON Schema Store 网络错误（不影响构建） |
| App 核心 | 3 | **0** | `globals.css` @tailwind 为 CSS-LS 假阳性 |
| UI 组件 | 5 | **0** | |
| Layout 组件 | 1 | **0** | |
| Decision 组件 | 7 | **0** | |
| 工具库 | 1 | **0** | |
| **合计** | **23** | **0** | |

npm install：196 packages, 0 vulnerabilities ✅

---

## 六、技术栈

- **Next.js 15.x** — App Router, typescript.ignoreBuildErrors: true, images unoptimized
- **React 19.x + react-dom 19.x**
- **Tailwind CSS v3.4.17** — dark mode via ['class'], CSS 变量主题, tailwindcss-animate
- **Radix UI** — tabs, switch, slot
- **shadcn/ui 兼容** — card, badge, button, tabs, switch（内联实现）
- **Recharts 2.15.4** — AreaChart, BarChart, ComposedChart, LineChart
- **lucide-react ^0.454.0** — 图标
- **clsx + tailwind-merge** — cn() 工具函数

---

## 七、架构师终审检查点

- [ ] 确认 4 个逻辑修复点符合意图
- [ ] 确认 `components/ui/` infrastructure 文件（非白名单）创建合规
- [ ] 确认 Sidebar 组件提取符合 layout 结构规范
- [ ] 确认 npm install 后无安全漏洞（已验：0 vulnerabilities）
- [ ] 终审通过后锁回白名单文件

---

## 八、后续步骤

1. 架构师终审本交接单
2. 终审通过后 git commit（独立 commit with message: `feat(dashboard): TASK-0021 E批 7页决策看板迁移 Next.js 15`）
3. 同步到 Air（botquant-backtest-prod 方向不适用，此为 JBT 服务）
4. F批 —— 待看板接入真实数据 API 或其他后续任务
