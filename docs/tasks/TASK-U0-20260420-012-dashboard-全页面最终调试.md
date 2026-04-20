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
