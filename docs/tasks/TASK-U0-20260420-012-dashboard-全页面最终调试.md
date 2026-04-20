# TASK-U0-20260420-012 Dashboard 全页面最终调试

## 任务信息

- 任务 ID：TASK-U0-20260420-012
- 任务名称：Dashboard 全页面最终调试
- 所属服务：dashboard
- 执行 Agent：Claude Code (U0 极速维修)
- 创建时间：2026-04-20
- 当前状态：进行中

## 任务目标

通过启动本地开发服务器，对看板的 28 个页面逐一进行最终调试和验收。

## 调试范围

### 1. 主页面（1 个）
- [ ] `/` - 聚合看板主页

### 2. 模拟交易看板（6 个）
- [ ] `/sim-trading` - 概览
- [ ] `/sim-trading/intelligence` - 风控监控
- [ ] `/sim-trading/operations` - 交易终端
- [ ] `/sim-trading/ctp-config` - CTP 配置
- [ ] `/sim-trading/risk-presets` - 风控预设
- [ ] `/sim-trading/market` - 市场行情

### 3. 决策看板（6 个）
- [ ] `/decision` - 概览
- [ ] `/decision/research` - 研究报告
- [ ] `/decision/repository` - 策略仓库
- [ ] `/decision/models` - 模型管理
- [ ] `/decision/signal` - 信号管理
- [ ] `/decision/reports` - 研报管理

### 4. 数据看板（3 个）
- [ ] `/data` - 概览
- [ ] `/data/collectors` - 采集器状态
- [ ] `/data/explorer` - 数据浏览器

### 5. 回测看板（5 个）
- [ ] `/backtest` - 概览
- [ ] `/backtest/operations` - 回测操作
- [ ] `/backtest/results` - 回测结果
- [ ] `/backtest/review` - 人工审核
- [ ] `/backtest/optimizer` - 参数优化

### 6. 研究员看板（1 个）
- [ ] `/researcher` - 研究员看板

### 7. 其他页面（6 个）
- [ ] `/settings` - 设置
- [ ] `/billing` - 计费
- [ ] `/login` - 登录
- [ ] 其他子页面...

## 调试检查项

每个页面需要检查：
1. ✅ 页面加载正常，无报错
2. ✅ 布局正确，响应式适配
3. ✅ 组件渲染正常（KPI 卡片、图表、列表等）
4. ✅ 透明效果和毛玻璃效果正确
5. ✅ 悬停动画流畅
6. ✅ API 调用正常（或 mock 数据显示正确）
7. ✅ 暗色主题显示正常
8. ✅ 侧边栏导航正常

## 开发环境

### 启动命令
```bash
cd /Users/jayshao/JBT/services/dashboard/dashboard_web
pnpm dev
```

### 访问地址
http://localhost:3005

### 环境变量
```bash
NEXT_PUBLIC_SIM_TRADING_URL=http://192.168.31.223:8101
NEXT_PUBLIC_DECISION_URL=http://192.168.31.142:8104
NEXT_PUBLIC_DATA_URL=http://192.168.31.76:8105
NEXT_PUBLIC_BACKTEST_URL=http://192.168.31.245:8103
```

## 问题记录

### 发现的问题
| 页面 | 问题描述 | 严重程度 | 状态 |
|------|---------|---------|------|
| 全局 | 硬编码颜色导致暗色/亮色模式不统一 | P0 | 修复中 |
| Researcher | bg-white/text-gray-* 硬编码（4个文件） | P0 | 待修复 |
| 图表组件 | Recharts 固定颜色值（8个文件） | P1 | 待修复 |
| 状态指示器 | bg-green-500/bg-red-500 硬编码（24个文件） | P1 | 待修复 |

### 修复记录
| 页面 | 修复内容 | 修改文件 | 完成时间 |
|------|---------|---------|---------|
| 全局 | 创建颜色修复计划 | TASK-U0-20260420-012-dashboard-颜色硬编码修复计划.md | 2026-04-20 |
| 全局 | 创建备份分支 | backup-dashboard-color-fix-20260420-190135 | 2026-04-20 |
| Researcher | 修复主页面硬编码颜色 | app/data/researcher/page.tsx | 2026-04-20 |
| Researcher | 修复 source-manager 硬编码颜色 | components/source-manager.tsx | 2026-04-20 |
| Researcher | 修复 priority-adjuster 硬编码颜色 | components/priority-adjuster.tsx | 2026-04-20 |
| Researcher | 修复 report-viewer 硬编码颜色 | components/report-viewer.tsx | 2026-04-20 |
| Settings | 修复设置页 bg-gray-950 遮住蜂窝背景 | app/(dashboard)/settings/layout.tsx | 2026-04-20 |
| Data | 数据端 overview/collectors/explorer/system-monitor/news-feed 清理暗色硬编码 | components/data/*.tsx | 2026-04-20 |
| 用户系统 | **完整用户认证系统**（Session Token + 路由保护 + 用户管理 UI） | 见下方详情 | 2026-04-20 |

### 用户认证系统修改详情（2026-04-20，commit 37c86bac2）

**后端 (`services/dashboard/src/main.py`)**：
- 新增 `sessions` SQLite 表（token、user_id、created_at、expires_at）
- 登录接口 `/auth/login` 返回 session token（`secrets.token_urlsafe(32)`，有效期30天）
- 新增 `/auth/me`（验证 token 返回当前用户）、`/auth/logout`（失效 session）
- 新增 `get_current_user`、`require_admin` FastAPI 依赖注入
- 用户管理端点（list/create/update/delete/password）全部加上管理员 session 认证
- 密码最小6位校验，`delete_user` 禁止删除自己，`update_user` 保护最后一个管理员

**前端**：
- `middleware.ts`：Next.js 边缘路由保护，未登录跳转 `/login`（读 `jbt_token` cookie）
- `lib/auth-context.tsx`：全局 `AuthProvider` + `useAuth` hook（user/token/isAdmin/logout）
- `lib/api/auth.ts`：新增 `getAuthHeaders()` 自动携带 Bearer token；登录响应含 token
- `app/layout.tsx`：注入 `AuthProvider` 包裹全局
- `app/(auth)/login/page.tsx`：登录成功存 token 到 cookie（`SameSite=Lax`）+ localStorage；inline 错误提示
- `app/(dashboard)/settings/page.tsx`：完整重写——Dialog 弹窗式用户管理 UI（添加/删除/改密码），useAuth 读取当前用户，管理员才显示用户列表，退出登录按钮

## 最近修改记录（2026-04-20 本轮）

### 登录修复与视觉升级（commit daffc4c04 / fe8ee3faf / 1766cbc02）

| 修改类别 | 文件 | 内容 |
|---------|------|------|
| 登录大小写不敏感 | `src/main.py` | `WHERE LOWER(username)=LOWER(?)` |
| 登录页左侧文字居中 | `login/page.tsx` | 加 `items-center justify-center w-full text-center` |
| 退出按钮接 logout | `app-sidebar.tsx` | 加 `useAuth`、`onClick={() => logout()}`，用户名/头像动态显示 |
| 登录页蜂窝背景 | `auth/layout.tsx` | 加 `AnimatedGridBg` + `.scan-line` 扫描亮条 |
| 登录页面板透明 | `login/page.tsx` | 去掉两侧不透明渐变背景 |
| 扫描亮条动画 | `globals.css` | 新增 `@keyframes scan-down` + `.scan-line` CSS |
| KPI 透明玻璃（亮色模式）| `globals.css` | `glass-card` 背景从 0.8→0.15，真正透明 |
| KPI 加 glass-card | `kpi-card.tsx`、`data-quality-kpi.tsx`、`data-source-health-kpi.tsx`、`decision/overview.tsx` | 所有 KPI Card 加 `glass-card` |
| 橙色呼吸增强 | `animated-grid-bg.tsx` | `BASE_A 0.05→0.07`，`SHIMMER_A 0.18→0.28`，`PULSE_PROB 0.025→0.04`，光晕强度 +60% |

### 验证结果（2026-04-20 最终）
- ✅ `pnpm build` 通过（exit 0）
- ✅ dev server 就绪（Ready in 3.5s，无 Error 日志）
- ✅ `/login` → HTTP 200，HTML 含 `AnimatedGridBg` + `scan-line`
- ✅ `/` → HTTP 307 重定向 `/login`（中间件认证正常）
- ✅ 无白屏风险（auth/layout.tsx 无 flex 嵌套，login 有 Suspense 包裹）

### Git 备份
- tag: `backup-auth-sidebar-20260420-220843`
- 最新 commit: `fe8ee3faf`

### 自动刷新卡死修复（2026-04-20 深夜补充）

| 修改类别 | 文件 | 内容 |
|---------|------|------|
| 头部对齐备份点 | `app-header.tsx`、`app-sidebar.tsx` | 已先独立提交为 `b06c8dc18`，用于回滚顶部线条/面包屑调整 |
| 去掉首页整页自动刷新 | `hooks/use-dashboard-data.ts` | 移除 `setInterval(fetchData, 30000)`，首页不再每 30 秒整页轮询 |
| refetch 改静默刷新 | `hooks/use-dashboard-data.ts` | `refetch()` 改为 silent 模式，不再切回整页 loading / Skeleton |
| KPI 独立静默刷新 | `hooks/use-dashboard-kpis.ts` | 新增独立 KPI 轮询 hook，仅刷新 `account / performance / risk` |
| 首页接入独立 KPI 数据源 | `app/(dashboard)/page.tsx` | KPI 卡片、收益图摘要、风险指标改用静默 KPI 快照，避免整页抖动 |

### 本轮问题根因
- 根因：首页 `useDashboardData` 每 30 秒执行一次整页级 `Promise.allSettled`，并先 `setLoading(true)`，导致页面重新进入 Skeleton/重建阶段；接口稍慢时会表现为页面卡死、无法点击。
- 修复策略：移除首页整页轮询，只保留 KPI 级静默轮询；手动刷新和下单后的 `refetch` 也改为静默更新。

### 本轮验证
- ✅ `pnpm tsc --noEmit` 通过
- ✅ `pnpm build` 通过
- ✅ `use-dashboard-data.ts` 中已无 30 秒自动轮询
- ✅ 首页 KPI 仍保留数据更新能力，但不再触发整页 loading 抖动

### 本轮回滚点
- 修复前备份 commit: `b06c8dc18`
- 修复前 tag: `backup-dashboard-header-align-20260420-*`

## 验收标准

- [ ] 所有 28 个页面加载正常
- [ ] 无控制台报错
- [ ] UI 显示符合设计规范
- [ ] 交互功能正常
- [ ] 性能表现良好（首屏加载 < 2s）

## 备注

- U0 极速维修模式，无需 Token
- 发现问题立即修复，记录在问题记录表中
- 修复完成后更新验收标准
