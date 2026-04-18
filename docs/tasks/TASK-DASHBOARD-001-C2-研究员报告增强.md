# TASK-DASHBOARD-001-C2：Data 研究员报告增强

## 任务信息

- 任务 ID：TASK-DASHBOARD-001-C2
- 上级任务：TASK-DASHBOARD-001（Dashboard 页面完成计划）
- 所属服务：data
- 执行 Agent：Livis（Claude-Code）
- 复核人：Atlas
- 优先级：P1
- 预计工期：0.5 天
- 当前状态：✅ 已完成（U0 紧急直修）
- 完成时间：2026-04-18

## 任务目标

为 Data 看板创建研究员报告展示页面，支持报告列表查看和详情展示。

## 背景

Data 服务后端已实现研究员报告 API：
- 路由：`services/data/src/api/routes/researcher_route.py`
- API 端点：
  - `GET /api/v1/researcher/report/latest` — 最新报告
  - `GET /api/v1/researcher/report/{date}` — 指定日期报告列表
  - `GET /api/v1/researcher/report/{date}/{segment}` — 指定报告详情
  - `GET /api/v1/researcher/status` — 研究员状态
  - `POST /api/v1/researcher/trigger` — 手动触发研究

但前端只有基础控制台，缺乏报告列表和详情展示功能。

## 功能需求

### 1. 报告列表页面
- 显示最近 7 天的研究员报告
- 按日期分组展示
- 每个报告显示时段标签（盘前/午间/盘后/夜盘）
- 点击报告卡片跳转到详情页

### 2. 报告详情页面
- 显示报告基本信息（报告 ID、时段、生成时间、模型）
- 期货市场 Tab：
  - 市场综述
  - 覆盖品种数量
  - 品种详情（如有）
- 股票市场 Tab：
  - 市场综述
  - 覆盖股票数量
  - 异动股票列表（如有）

### 3. API 客户端
- 封装所有研究员 API 端点
- 完整 TypeScript 类型定义
- 统一错误处理

## 文件清单（4 个文件）

### 新建文件

1. `services/data/data_web/app/researcher/reports/page.tsx`
   - 报告列表页面
   - 显示最近 7 天报告
   - 按日期分组展示

2. `services/data/data_web/app/researcher/reports/[date]/[id]/page.tsx`
   - 报告详情页面
   - 动态路由（date + segment）
   - 集成 ResearchReport 组件

3. `services/data/data_web/components/researcher/ResearchReport.tsx`
   - 报告展示组件
   - 期货/股票双 Tab
   - 报告概览卡片

4. `services/data/data_web/lib/api/researcher.ts`
   - researcher API 客户端
   - 封装 5 个 API 端点

## 技术实现

### API 客户端设计

```typescript
export const researcherApi = {
  getLatestReport: () => apiFetch<ResearchReport>(`/api/data/api/v1/researcher/report/latest`),
  getReportsByDate: (date: string) => apiFetch<{ date: string; segments: ReportListItem[] }>(`/api/data/api/v1/researcher/report/${date}`),
  getReportByDateSegment: (date: string, segment: string) => apiFetch<ResearchReport>(`/api/data/api/v1/researcher/report/${date}/${segment}`),
  getStatus: () => apiFetch<ResearcherStatus>(`/api/data/api/v1/researcher/status`),
  triggerResearch: (segment: string) => apiFetch<any>(`/api/data/api/v1/researcher/trigger?segment=${segment}`, { method: "POST" }),
}
```

### 动态路由设计

- 列表页：`/researcher/reports`
- 详情页：`/researcher/reports/[date]/[id]`
  - 示例：`/researcher/reports/2026-04-18/盘前`

### 数据获取策略

- 列表页：并行获取最近 7 天报告（`Promise.allSettled`）
- 详情页：根据 URL 参数获取指定报告
- 错误处理：跳过无法获取的日期，只显示有效报告

### UI 组件库

- shadcn/ui：Card、Tabs、Badge、Button
- Next.js：动态路由、useParams、useRouter
- 响应式布局：grid + flex

## 验收标准

- [x] 报告列表页正确显示最近 7 天报告
- [x] 报告按日期分组展示
- [x] 点击报告卡片正确跳转到详情页
- [x] 详情页正确显示报告基本信息
- [x] 期货市场 Tab 正确显示市场综述和品种详情
- [x] 股票市场 Tab 正确显示市场综述和异动股票
- [x] 动态路由正确解析 date 和 segment 参数
- [x] TypeScript 类型定义完整
- [x] 错误处理和加载状态完善

## 执行记录

### U0 紧急直修模式（2026-04-18）

**执行人**：Livis Claude  
**执行时间**：2026-04-18  
**执行模式**：U0（无 Token，紧急直修）

#### 完成内容

1. ✅ 创建 `app/researcher/reports/page.tsx`（列表页，80 行）
   - 并行获取最近 7 天报告
   - 按日期分组展示
   - 报告卡片支持点击跳转
   - 返回控制台按钮

2. ✅ 创建 `app/researcher/reports/[date]/[id]/page.tsx`（详情页，60 行）
   - 动态路由解析 date 和 segment
   - 集成 ResearchReport 组件
   - 返回按钮

3. ✅ 创建 `components/researcher/ResearchReport.tsx`（报告组件，150 行）
   - 报告概览卡片（报告 ID/时段/生成时间/模型）
   - 期货市场 Tab（市场综述 + 品种详情）
   - 股票市场 Tab（市场综述 + 异动股票）
   - 响应式布局

4. ✅ 创建 `lib/api/researcher.ts`（API 客户端，50 行）
   - 封装 5 个 API 端点
   - 完整 TypeScript 类型定义
   - 统一错误处理

#### Commit 信息

- Commit Hash: `80283c806`
- Commit Message: `U0: C1+C2 LLM计费展示 + 研究员报告增强`
- 文件数: 4 个（C2 部分）
- 代码行数: ~340 行

#### 技术亮点

- ✅ 完整对接后端 API（5 个端点全部对接）
- ✅ 动态路由（Next.js App Router）
- ✅ 并行数据获取（Promise.allSettled）
- ✅ 响应式布局（grid + flex，适配移动端）
- ✅ 完整类型定义（ResearchReport、ReportListItem、ResearcherStatus）
- ✅ 错误处理（try-catch + 加载状态 + 空数据提示）
- ✅ 双 Tab 展示（期货/股票分离）

## 后续优化建议

### P2 优化项（可选）

1. **报告导出功能**
   - 支持导出报告为 PDF
   - 支持导出报告为 Markdown
   - 支持批量导出

2. **报告搜索功能**
   - 按时段筛选（盘前/午间/盘后/夜盘）
   - 按日期范围筛选
   - 按品种搜索

3. **报告订阅功能**
   - 订阅特定时段报告
   - 飞书/邮件推送
   - 自定义推送频率

4. **报告可视化增强**
   - 添加 K 线图
   - 添加成交量图
   - 添加情绪热力图
   - 添加事件时间轴

5. **报告生成器增强（后端）**
   - 多维度数据分析（价格/成交量/持仓/情绪）
   - 关键事件提取与标注
   - 市场异动检测与解读
   - 趋势预测与风险提示

## 依赖关系

### 前置依赖
- ✅ Data 后端 researcher API 已实现
- ✅ Data 后端 researcher 路由已注册

### 后置依赖
- 无

## 风险与问题

### 已解决问题
- ✅ 后端 API 路径确认（`/api/data/api/v1/researcher/*`）
- ✅ 动态路由参数确认（date + segment）
- ✅ 报告数据结构确认（futures_summary + stocks_summary）

### 已知限制
- 当前报告内容较简陋（后端 report_generator.py 功能简单）
- 品种详情和异动股票数据可能为空
- 需要后续增强报告生成器（见后续优化建议）

## 治理记录

### U0 执行说明

本任务采用 U0 紧急直修模式执行，原因：
1. Jay.S 明确指令"C1、C2 U0完成"
2. 后端 API 已实现，前端只需对接
3. 功能范围明确，风险可控
4. 用户明确要求"重点开发数据研究员系统"

### 事后补建任务文档

本任务文档为事后补建，记录实际执行情况，供 Atlas 回归后审核。

---

**创建人**：Livis Claude  
**创建时间**：2026-04-18（事后补建）  
**执行时间**：2026-04-18  
**完成状态**：✅ 已完成
