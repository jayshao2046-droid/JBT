# Dashboard 颜色硬编码修复计划

## 问题总结

扫描发现 **100+ 处硬编码颜色**，导致暗色/亮色模式不统一。

## 问题分类

### 1. 图表组件硬编码（9 个文件）
**问题**：Recharts 图表使用固定颜色值（如 `#8884d8`、`#82ca9d`），不响应主题切换。

| 文件 | 硬编码颜色 | 影响 |
|------|-----------|------|
| `components/billing/CostTrendChart.tsx` | `#8884d8`, `#82ca9d` | 成本趋势图 |
| `components/billing/TokenUsageChart.tsx` | `#8884d8`, `#82ca9d`, `#ffc658` | Token 使用图 |
| `components/sim-trading/kline-chart.tsx` | `#8884d8`, `#82ca9d` | K 线图 |
| `components/sim-trading/technical-chart.tsx` | 待检查 | 技术指标图 |
| `components/sim-trading/trade-heatmap.tsx` | 待检查 | 交易热力图 |
| `components/dashboard/churn-chart.tsx` | `#f97316` | 流失率图 |
| `components/dashboard/equity-chart.tsx` | `#8884d8` | 权益曲线 |
| `components/backtest/equity-curve-chart.tsx` | `#8884d8` | 回测权益曲线 |

**修复方案**：使用 CSS 变量 `hsl(var(--chart-1))`、`hsl(var(--chart-2))` 等。

### 2. Researcher 页面硬编码（1 个文件 + 3 个子组件）
**问题**：`app/data/researcher/page.tsx` 及其子组件大量使用 `bg-white`、`text-gray-600` 等固定颜色。

| 文件 | 硬编码类型 | 数量 |
|------|-----------|------|
| `app/data/researcher/page.tsx` | `bg-white`, `text-gray-*`, `bg-green-500`, `bg-red-500` | 20+ |
| `components/source-manager.tsx` | `bg-blue-100`, `bg-green-100`, `text-gray-*` | 15+ |
| `components/priority-adjuster.tsx` | `bg-white`, `bg-gray-*`, `bg-red-100`, `bg-yellow-100` | 20+ |
| `components/report-viewer.tsx` | `bg-blue-500`, `bg-gray-*`, `text-gray-*` | 15+ |

**修复方案**：
- `bg-white` → `bg-card`
- `text-gray-600` → `text-muted-foreground`
- `bg-green-500` → `bg-green-500/20` + `text-green-400`（使用透明度）
- `bg-red-500` → `bg-red-500/20` + `text-red-400`

### 3. 状态指示器硬编码（24 个文件）
**问题**：状态指示器（绿色=正常、红色=错误、黄色=警告）使用固定颜色类。

**常见模式**：
```tsx
// ❌ 错误写法
className={status === "success" ? "bg-green-500" : "bg-red-500"}

// ✅ 正确写法
className={status === "success" ? "bg-green-500/20 text-green-400 border-green-500/30" : "bg-red-500/20 text-red-400 border-red-500/30"}
```

**影响文件**：
- `components/layout/app-header.tsx`
- `components/layout/app-sidebar.tsx`
- `components/data/overview-page.tsx`
- `components/data/collectors-page.tsx`
- `components/data/system-monitor.tsx`
- `components/data/news-feed.tsx`
- `components/dashboard/current-positions.tsx`
- `components/dashboard/data-source-status.tsx`
- `app/(dashboard)/page.tsx`
- `app/(dashboard)/sim-trading/page.tsx`
- 等 14+ 个文件

**修复方案**：统一使用透明度 + 语义化颜色变量。

### 4. 内联样式硬编码（2 个文件）
**问题**：使用 `style={{ borderLeftColor: "#10b981" }}` 等内联样式。

| 文件 | 位置 | 硬编码值 |
|------|------|---------|
| `app/data/researcher/page.tsx` | 第 85 行 | `#10b981`, `#ef4444` |
| `components/backtest/result-detail-dialog.tsx` | 待检查 | 待确认 |

**修复方案**：改用 Tailwind 类或 CSS 变量。

## 修复优先级

### P0（必须修复，影响主题切换）
1. ✅ Researcher 页面及子组件（用户最常访问）
2. ✅ 主页面状态指示器（`app/(dashboard)/page.tsx`）
3. ✅ 数据看板状态指示器（`components/data/*`）

### P1（重要，影响视觉一致性）
4. ⏳ 图表组件（Recharts 颜色）
5. ⏳ 侧边栏状态指示器
6. ⏳ 其他页面状态指示器

### P2（可选，影响较小）
7. ⏳ 内联样式硬编码
8. ⏳ 注释中的颜色说明（不影响功能）

## 修复标准

### 颜色映射表

| 旧类名 | 新类名 | 说明 |
|--------|--------|------|
| `bg-white` | `bg-card` | 卡片背景 |
| `text-gray-600` | `text-muted-foreground` | 次要文本 |
| `text-gray-900` | `text-foreground` | 主要文本 |
| `bg-green-500` | `bg-green-500/20 text-green-400 border-green-500/30` | 成功状态 |
| `bg-red-500` | `bg-red-500/20 text-red-400 border-red-500/30` | 错误状态 |
| `bg-yellow-500` | `bg-yellow-500/20 text-yellow-400 border-yellow-500/30` | 警告状态 |
| `bg-blue-500` | `bg-blue-500/20 text-blue-400 border-blue-500/30` | 信息状态 |

### Recharts 颜色映射

| 旧颜色 | 新颜色 | CSS 变量 |
|--------|--------|---------|
| `#8884d8` | `hsl(var(--chart-1))` | 主色 |
| `#82ca9d` | `hsl(var(--chart-2))` | 次色 |
| `#ffc658` | `hsl(var(--chart-4))` | 强调色 |
| `#f97316` | `hsl(var(--primary))` | 主题色 |

## 验收标准

- [ ] 所有页面在暗色模式下无白色闪烁
- [ ] 所有状态指示器在两种模式下清晰可见
- [ ] 所有图表颜色响应主题切换
- [ ] 无硬编码颜色值（`#xxx`、`rgb()`、`rgba()`）
- [ ] 无固定 Tailwind 颜色类（`bg-white`、`text-gray-600` 等）
- [ ] ESLint 无警告
- [ ] 构建成功

## 修复进度

- [ ] P0: Researcher 页面（0/4 文件）
- [ ] P0: 主页面状态指示器（0/1 文件）
- [ ] P0: 数据看板状态指示器（0/3 文件）
- [ ] P1: 图表组件（0/8 文件）
- [ ] P1: 其他状态指示器（0/14 文件）
- [ ] P2: 内联样式（0/2 文件）

## 备注

- 修复过程中保持 git 提交粒度，每修复一个文件提交一次
- 修复后立即在浏览器中验证暗色/亮色模式切换效果
- 发现新问题立即记录到此文档
