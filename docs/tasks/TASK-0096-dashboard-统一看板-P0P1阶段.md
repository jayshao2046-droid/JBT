# TASK-0096 dashboard 统一看板 P0+P1 — 基础架构 + 认证 + 首页 + 导航

## 元信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0096 |
| 任务名称 | dashboard 统一看板 P0+P1 — 基础架构、认证框架、首页总控台、统一导航 |
| 服务归属 | `services/dashboard/` |
| 前端子目录 | `services/dashboard/dashboard_web/`（全新建立） |
| 优先级 | P0+P1 |
| 状态 | whitelist_amended |
| 创建人 | Atlas |
| 创建时间 | 2026-04-13 |
| 执行人 | Claude（当前会话） |
| 依赖 | TASK-0085~0095 全部 locked（✅ 已满足） |

---

## 任务背景

Jay.S 于 2026-04-13 明确授权：

1. 服务归属确认：统一看板使用 `services/dashboard/`（方案 A），不新建 `services/portal/`
2. 将四端临时看板（sim-trading_web / backtest_web / decision_web / data_web）整合为统一门户网站
3. 新增登录页、首页总控台、系统设置页三个核心入口层页面
4. 执行主体：Claude（当前 Atlas 窗口）

设计参考文档：`docs/portal-design/`（已有完整设计方案）

---

## 任务边界（P0+P1）

### 包含

- 初始化 `services/dashboard/dashboard_web/` Next.js 15 项目
- 基础项目配置：package.json、tsconfig、next.config、tailwind、postcss、eslint
- 全局样式与 shadcn/ui 基础组件（button、card、input、label、separator、badge、dropdown、avatar、tabs、switch）
- 统一布局组件：sidebar、topbar、nav-item
- 认证框架：LOGIN 页（`/login`）+ auth 路由组 layout
- 首页总控台（`/`）：四端服务状态概览卡片
- 系统设置页（`/settings`）：基础配置入口
- lib：auth.ts、api-client.ts、utils.ts、constants.ts
- types/index.ts

### 排除（留待后续批次）

- 四端页面迁移（P2，TASK-0097）
- API 代理配置（P3，TASK-0098）
- 后端 Python 服务（`services/dashboard/src/**`，本轮不动）
- `.env.example`、`Dockerfile`（P0 保护路径，本轮不动）

---

## 验收标准

1. `pnpm build` 在 `services/dashboard/dashboard_web/` 目录下执行成功，无 TypeScript 错误
2. 构建产出包含：`/login`、`/`（首页）、`/settings` 三个路由
3. 编辑器静态诊断（`get_errors`）无红色错误
4. 所有新建文件通过 ESLint 检查

---

## 文件白名单（P0+P1，共 39 个文件）

> **⚠️ 白名单修订记录（2026-04-13，Atlas）**：
> - ✅ 新增：`services/dashboard/dashboard_web/tailwind.config.ts`（shadcn/ui CSS 变量系统必需，pnpm build 验证通过后补入）
> - ❌ 移除：`services/dashboard/dashboard_web/app/page.tsx`（实施过程确认根路由重定向由路由组 `(dashboard)/page.tsx` 承担，独立根 page.tsx 已删除，无遗留代码）

### 项目配置文件（8 个）
```
services/dashboard/dashboard_web/package.json
services/dashboard/dashboard_web/pnpm-lock.yaml
services/dashboard/dashboard_web/tsconfig.json
services/dashboard/dashboard_web/next.config.ts
services/dashboard/dashboard_web/tailwind.config.ts
services/dashboard/dashboard_web/postcss.config.mjs
services/dashboard/dashboard_web/eslint.config.mjs
services/dashboard/dashboard_web/.gitignore
```

### 全局样式 & 根 layout（2 个）
```
services/dashboard/dashboard_web/app/globals.css
services/dashboard/dashboard_web/app/layout.tsx
```

### 认证路由组（3 个）
```
services/dashboard/dashboard_web/app/(auth)/layout.tsx
services/dashboard/dashboard_web/app/(auth)/login/page.tsx
services/dashboard/dashboard_web/app/(auth)/login/layout.tsx
```

### Dashboard 路由组（4 个）
```
services/dashboard/dashboard_web/app/(dashboard)/layout.tsx
services/dashboard/dashboard_web/app/(dashboard)/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/settings/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/settings/layout.tsx
```

### UI 基础组件（11 个）
```
services/dashboard/dashboard_web/components/ui/button.tsx
services/dashboard/dashboard_web/components/ui/card.tsx
services/dashboard/dashboard_web/components/ui/input.tsx
services/dashboard/dashboard_web/components/ui/label.tsx
services/dashboard/dashboard_web/components/ui/separator.tsx
services/dashboard/dashboard_web/components/ui/badge.tsx
services/dashboard/dashboard_web/components/ui/dropdown-menu.tsx
services/dashboard/dashboard_web/components/ui/avatar.tsx
services/dashboard/dashboard_web/components/ui/tabs.tsx
services/dashboard/dashboard_web/components/ui/switch.tsx
services/dashboard/dashboard_web/components/ui/scroll-area.tsx
```

### 布局组件（3 个）
```
services/dashboard/dashboard_web/components/layout/sidebar.tsx
services/dashboard/dashboard_web/components/layout/topbar.tsx
services/dashboard/dashboard_web/components/layout/nav-item.tsx
```

### 首页组件（3 个）
```
services/dashboard/dashboard_web/components/dashboard/service-status-card.tsx
services/dashboard/dashboard_web/components/dashboard/status-overview.tsx
services/dashboard/dashboard_web/components/dashboard/quick-links.tsx
```

### Lib & Types（4 个）
```
services/dashboard/dashboard_web/lib/auth.ts
services/dashboard/dashboard_web/lib/api-client.ts
services/dashboard/dashboard_web/lib/utils.ts
services/dashboard/dashboard_web/lib/constants.ts
services/dashboard/dashboard_web/types/index.ts
```

> **说明**：dashboard_web 为全新目录，所有文件均为新建。如实施过程发现需要超出白名单的新文件，必须停止并向 Atlas 申请补签。

---

## 修订历史

| 日期 | 修订人 | 内容 |
|------|--------|------|
| 2026-04-13 | Atlas | 白名单修订：新增 tailwind.config.ts（1 个），移除 app/page.tsx（1 个），计数由 38→39 |

> **修订依据**：第 4 轮终审发现 shadcn/ui 的 `border-border` CSS 变量需要 `tailwind.config.ts` 方可解析，否则构建失败。Claude 已添加该文件并通过 `pnpm build` 验证。`app/page.tsx` 根路由文件在实施中确认不需要（路由组 `(dashboard)/page.tsx` 直接承接 `/` 路由），已删除，故同步从白名单移除。

---

## 相关文档

- 设计方案：`docs/portal-design/统一门户系统设计方案-登录页-首页-系统设置页.md`
- 技术方案：`docs/portal-design/四端看板合并统一网站-技术调整方案.md`
- 后续任务：TASK-0097（P2 四端页面迁移）、TASK-0098（P3 API 代理+测试）
