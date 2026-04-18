# TASK-DASHBOARD-001-C1：Decision LLM 计费展示页面

## 任务信息

- 任务 ID：TASK-DASHBOARD-001-C1
- 上级任务：TASK-DASHBOARD-001（Dashboard 页面完成计划）
- 所属服务：decision
- 执行 Agent：Livis（Claude-Code）
- 复核人：Atlas
- 优先级：P1
- 预计工期：0.5 天
- 当前状态：✅ 已完成（U0 紧急直修）
- 完成时间：2026-04-18

## 任务目标

为 Decision 看板创建 LLM 计费展示页面，实时显示 Token 消费和成本统计。

## 背景

Decision 服务后端已完整实现 LLM 计费追踪系统：
- 文件：`services/decision/src/llm/billing.py`（完整计费追踪器）
- 路由：`services/decision/src/api/routes/billing.py`（已注册）
- API 端点：
  - `GET /api/v1/billing/hourly` — 当前小时统计
  - `GET /api/v1/billing/daily` — 今日累计统计
  - `GET /api/v1/billing/records` — 最近原始记录
  - `POST /api/v1/billing/report` — 立即推送飞书报告

但前端完全缺失，无法查看实时 Token 消费和成本统计。

## 功能需求

### 1. 计费统计主页面
- 显示当前小时 Token 消费和成本
- 显示今日累计 Token 消费和成本
- 显示预算进度（今日预算使用百分比）
- 30 秒自动刷新

### 2. Token 消费趋势图
- 折线图展示最近 50 次调用的 Token 消费
- 区分输入 Token、输出 Token、总计
- 时间轴显示调用时间

### 3. 成本趋势图
- 柱状图展示最近 50 次调用的成本
- 区分输入成本、输出成本
- 支持悬停查看详细数据

### 4. 用量详情表格
- 表格展示最近 100 次调用记录
- 显示时间、模型、组件、层级、Token 数、成本、本地/在线标识
- 支持滚动查看

## 文件清单（5 个文件）

### 新建文件

1. `services/decision/decision_web/app/billing/page.tsx`
   - 计费统计主页面
   - 集成三个统计卡片 + 三个 Tab（Token 消费/成本趋势/用量详情）

2. `services/decision/decision_web/components/billing/TokenUsageChart.tsx`
   - Token 消费趋势折线图组件
   - 使用 recharts LineChart

3. `services/decision/decision_web/components/billing/CostTrendChart.tsx`
   - 成本趋势柱状图组件
   - 使用 recharts BarChart

4. `services/decision/decision_web/components/billing/UsageBreakdown.tsx`
   - 用量详情表格组件
   - 使用 shadcn/ui Table

5. `services/decision/decision_web/lib/api/billing.ts`
   - billing API 客户端
   - 封装 4 个 API 端点

## 技术实现

### API 客户端设计

```typescript
export const billingApi = {
  getHourlySummary: () => apiFetch<HourlySummary>(`/api/decision/api/v1/billing/hourly`),
  getDailySummary: () => apiFetch<DailySummary>(`/api/decision/api/v1/billing/daily`),
  getRecords: (limit = 100) => apiFetch<{ records: BillingRecord[] }>(`/api/decision/api/v1/billing/records?limit=${limit}`),
  sendReport: () => apiFetch<{ sent: boolean }>(`/api/decision/api/v1/billing/report`, { method: "POST" }),
}
```

### 数据刷新策略

- 主页面：30 秒自动刷新
- 图表组件：30 秒自动刷新
- 表格组件：30 秒自动刷新
- 使用 `useEffect` + `setInterval` 实现

### UI 组件库

- shadcn/ui：Card、Tabs、Table、Badge
- recharts：LineChart、BarChart
- 响应式布局：grid + flex

## 验收标准

- [x] 主页面正确显示当前小时/今日累计/预算进度
- [x] Token 消费趋势图正确显示最近 50 次调用
- [x] 成本趋势图正确显示输入/输出成本
- [x] 用量详情表格正确显示最近 100 次调用记录
- [x] 所有数据 30 秒自动刷新
- [x] 响应式布局适配移动端
- [x] TypeScript 类型定义完整
- [x] 错误处理和加载状态完善

## 执行记录

### U0 紧急直修模式（2026-04-18）

**执行人**：Livis Claude  
**执行时间**：2026-04-18  
**执行模式**：U0（无 Token，紧急直修）

#### 完成内容

1. ✅ 创建 `app/billing/page.tsx`（主页面，130 行）
   - 实现三个统计卡片（当前小时/今日累计/预算进度）
   - 集成三个 Tab（Token 消费/成本趋势/用量详情）
   - 30 秒自动刷新

2. ✅ 创建 `components/billing/TokenUsageChart.tsx`（折线图，70 行）
   - 使用 recharts LineChart
   - 显示输入/输出/总计三条折线
   - 最近 50 次调用数据

3. ✅ 创建 `components/billing/CostTrendChart.tsx`（柱状图，70 行）
   - 使用 recharts BarChart
   - 显示输入成本/输出成本双柱
   - 最近 50 次调用数据

4. ✅ 创建 `components/billing/UsageBreakdown.tsx`（表格，110 行）
   - 使用 shadcn/ui Table
   - 显示 8 列数据（时间/模型/组件/层级/输入Token/输出Token/成本/本地标识）
   - 最近 100 次调用记录
   - 支持滚动查看

5. ✅ 创建 `lib/api/billing.ts`（API 客户端，40 行）
   - 封装 4 个 API 端点
   - 完整 TypeScript 类型定义
   - 统一错误处理

#### Commit 信息

- Commit Hash: `80283c806`
- Commit Message: `U0: C1+C2 LLM计费展示 + 研究员报告增强`
- 文件数: 5 个（C1 部分）
- 代码行数: ~420 行

#### 技术亮点

- ✅ 完整对接后端 API（4 个端点全部对接）
- ✅ 30 秒自动刷新（所有组件统一刷新策略）
- ✅ 响应式布局（grid + flex，适配移动端）
- ✅ 完整类型定义（BillingRecord、HourlySummary、DailySummary）
- ✅ 错误处理（try-catch + 加载状态 + 空数据提示）
- ✅ 图表可视化（recharts LineChart + BarChart）
- ✅ 表格展示（shadcn/ui Table + Badge）

## 后续优化建议

### P2 优化项（可选）

1. **导出功能**
   - 支持导出用量报告为 CSV/Excel
   - 支持自定义时间范围导出

2. **筛选功能**
   - 按模型筛选（qwen-plus/qwen-max/本地模型）
   - 按组件筛选（策略生成/信号分析/报告生成）
   - 按时间范围筛选

3. **成本预警**
   - 设置每日预算阈值
   - 超过阈值时显示警告
   - 支持飞书/邮件通知

4. **历史趋势**
   - 显示最近 7 天/30 天成本趋势
   - 对比不同时间段的用量

## 依赖关系

### 前置依赖
- ✅ Decision 后端 billing API 已实现
- ✅ Decision 后端 billing 路由已注册

### 后置依赖
- 无

## 风险与问题

### 已解决问题
- ✅ 后端 API 路径确认（`/api/decision/api/v1/billing/*`）
- ✅ 数据刷新策略确认（30 秒统一刷新）
- ✅ 图表库选型确认（recharts）

### 无风险
- 后端 API 已完整实现，无需等待
- 前端组件独立，无跨服务依赖

## 治理记录

### U0 执行说明

本任务采用 U0 紧急直修模式执行，原因：
1. Jay.S 明确指令"C1、C2 U0完成"
2. 后端 API 已完整实现，前端只需对接
3. 功能范围明确，风险可控
4. 用户明确要求"确保在线模型 Token 消费记录真实体现"

### 事后补建任务文档

本任务文档为事后补建，记录实际执行情况，供 Atlas 回归后审核。

---

**创建人**：Livis Claude  
**创建时间**：2026-04-18（事后补建）  
**执行时间**：2026-04-18  
**完成状态**：✅ 已完成
