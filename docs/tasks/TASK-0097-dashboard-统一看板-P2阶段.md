# TASK-0097 dashboard 统一看板 P2 — 四端页面迁移整合

## 元信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0097 |
| 任务名称 | dashboard 统一看板 P2 — 四端页面迁移整合 |
| 服务归属 | `services/dashboard/` |
| 前端子目录 | `services/dashboard/dashboard_web/` |
| 优先级 | P2 |
| 状态 | review_approved |
| 创建人 | Atlas |
| 创建时间 | 2026-04-13 |
| 执行人 | Claude（当前会话） |
| 依赖 | TASK-0096 locked |

---

## 任务边界（P2）

将现有四端临时看板页面及组件迁移/整合到 `dashboard_web` 统一前端。

### 目标路由结构
```
/sim-trading/operations      ← 来自 sim-trading_web/app/operations/
/sim-trading/intelligence    ← 来自 sim-trading_web/app/intelligence/
/sim-trading/market          ← 来自 sim-trading_web/app/market/
/sim-trading/ctp-config      ← 来自 sim-trading_web/app/ctp-config/
/sim-trading/risk-presets    ← 来自 sim-trading_web/app/risk-presets/

/backtest/operations         ← 来自 backtest_web
/backtest/review             ← 来自 backtest_web
/backtest/agent-network      ← 来自 backtest_web
/backtest/history            ← 来自 backtest_web
/backtest/optimizer          ← 来自 backtest_web

/decision/operations         ← 来自 decision_web
/decision/research           ← 来自 decision_web
/decision/history            ← 来自 decision_web
/decision/optimizer          ← 来自 decision_web

/data/operations             ← 来自 data_web
/data/quality                ← 来自 data_web
/data/collectors             ← 来自 data_web
/data/history                ← 来自 data_web
/data/optimizer              ← 来自 data_web
```

### 包含
- 四端页面文件迁移（page.tsx + 页面级组件）
- 各端共享 UI 组件（chart、table 等）迁移到 dashboard_web/components/ 对应子目录
- API fetch hooks / SWR hooks 迁移

### 排除
- 各端 Python 后端代码（不触碰）
- 各端原有 `*_web/` 目录（只读参考，不删除）

---

## 验收标准

1. `pnpm build` 成功，所有四端路由均在产出中
2. 编辑器静态诊断无红色错误
3. 四端页面在 dashboard_web 内可独立导航（通过统一 sidebar nav）

---

## 文件白名单（P2，共 147 个文件）

> **白名单确认时间**：2026-04-13（TASK-0096 locked 后，Token 签发前），REVIEW-TASK-0097 通过。

### 配置文件更新（3 个）
```
services/dashboard/dashboard_web/package.json
services/dashboard/dashboard_web/pnpm-lock.yaml
services/dashboard/dashboard_web/next.config.ts
```

### 修改已有布局（1 个）
```
services/dashboard/dashboard_web/components/layout/sidebar.tsx
```

### 新增 UI 组件（23 个）
```
services/dashboard/dashboard_web/components/ui/accordion.tsx
services/dashboard/dashboard_web/components/ui/alert.tsx
services/dashboard/dashboard_web/components/ui/alert-dialog.tsx
services/dashboard/dashboard_web/components/ui/chart.tsx
services/dashboard/dashboard_web/components/ui/checkbox.tsx
services/dashboard/dashboard_web/components/ui/collapsible.tsx
services/dashboard/dashboard_web/components/ui/command.tsx
services/dashboard/dashboard_web/components/ui/dialog.tsx
services/dashboard/dashboard_web/components/ui/drawer.tsx
services/dashboard/dashboard_web/components/ui/form.tsx
services/dashboard/dashboard_web/components/ui/popover.tsx
services/dashboard/dashboard_web/components/ui/progress.tsx
services/dashboard/dashboard_web/components/ui/radio-group.tsx
services/dashboard/dashboard_web/components/ui/select.tsx
services/dashboard/dashboard_web/components/ui/sheet.tsx
services/dashboard/dashboard_web/components/ui/skeleton.tsx
services/dashboard/dashboard_web/components/ui/slider.tsx
services/dashboard/dashboard_web/components/ui/sonner.tsx
services/dashboard/dashboard_web/components/ui/table.tsx
services/dashboard/dashboard_web/components/ui/textarea.tsx
services/dashboard/dashboard_web/components/ui/toast.tsx
services/dashboard/dashboard_web/components/ui/toaster.tsx
services/dashboard/dashboard_web/components/ui/tooltip.tsx
```

### 模拟交易路由页面（6 个）
```
services/dashboard/dashboard_web/app/(dashboard)/sim-trading/operations/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/sim-trading/intelligence/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/sim-trading/intelligence/loading.tsx
services/dashboard/dashboard_web/app/(dashboard)/sim-trading/market/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/sim-trading/ctp-config/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/sim-trading/risk-presets/page.tsx
```

### 回测路由页面（10 个）
```
services/dashboard/dashboard_web/app/(dashboard)/backtest/operations/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/backtest/review/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/backtest/agent-network/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/backtest/agent-network/loading.tsx
services/dashboard/dashboard_web/app/(dashboard)/backtest/intelligence/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/backtest/intelligence/loading.tsx
services/dashboard/dashboard_web/app/(dashboard)/backtest/systems/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/backtest/results/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/backtest/optimizer/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/backtest/command-center/page.tsx
```

### 决策路由页面（5 个）
```
services/dashboard/dashboard_web/app/(dashboard)/decision/research/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/decision/history/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/decision/optimizer/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/decision/reports/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/decision/import/page.tsx
```

### 数据路由页面（10 个）
```
services/dashboard/dashboard_web/app/(dashboard)/data/operations/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/data/history/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/data/collections/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/data/systems/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/data/optimizer/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/data/command-center/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/data/agent-network/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/data/agent-network/loading.tsx
services/dashboard/dashboard_web/app/(dashboard)/data/intelligence/page.tsx
services/dashboard/dashboard_web/app/(dashboard)/data/intelligence/loading.tsx
```

### 模拟交易业务组件（13 个）
```
services/dashboard/dashboard_web/components/sim-trading/ConnectionQuality.tsx
services/dashboard/dashboard_web/components/sim-trading/ExecutionQualityKPI.tsx
services/dashboard/dashboard_web/components/sim-trading/KeyboardShortcutsHelp.tsx
services/dashboard/dashboard_web/components/sim-trading/MarketMovers.tsx
services/dashboard/dashboard_web/components/sim-trading/OrderFlowEnhanced.tsx
services/dashboard/dashboard_web/components/sim-trading/PerformanceKPI.tsx
services/dashboard/dashboard_web/components/sim-trading/PositionAnalysis.tsx
services/dashboard/dashboard_web/components/sim-trading/QuickOrderPresets.tsx
services/dashboard/dashboard_web/components/sim-trading/RiskConfigEditor.tsx
services/dashboard/dashboard_web/components/sim-trading/RiskTemplates.tsx
services/dashboard/dashboard_web/components/sim-trading/TechnicalChart.tsx
services/dashboard/dashboard_web/components/sim-trading/TradeHeatmap.tsx
services/dashboard/dashboard_web/components/sim-trading/ThemeToggle.tsx
```

### 回测业务组件（16 个）
```
services/dashboard/dashboard_web/components/backtest/BacktestAnalysis.tsx
services/dashboard/dashboard_web/components/backtest/BacktestComparison.tsx
services/dashboard/dashboard_web/components/backtest/BacktestConfigEditor.tsx
services/dashboard/dashboard_web/components/backtest/BacktestHeatmap.tsx
services/dashboard/dashboard_web/components/backtest/BacktestQualityKPI.tsx
services/dashboard/dashboard_web/components/backtest/BacktestQueue.tsx
services/dashboard/dashboard_web/components/backtest/BacktestTemplates.tsx
services/dashboard/dashboard_web/components/backtest/EquityCurveChart.tsx
services/dashboard/dashboard_web/components/backtest/KeyboardShortcutsHelp.tsx
services/dashboard/dashboard_web/components/backtest/ParamInput.tsx
services/dashboard/dashboard_web/components/backtest/ParameterOptimizer.tsx
services/dashboard/dashboard_web/components/backtest/PerformanceKPI.tsx
services/dashboard/dashboard_web/components/backtest/ProgressTracker.tsx
services/dashboard/dashboard_web/components/backtest/ReviewPanel.tsx
services/dashboard/dashboard_web/components/backtest/StockReviewTable.tsx
services/dashboard/dashboard_web/components/backtest/TradeDetailAnalysis.tsx
```

### 决策业务组件（29 个）
```
services/dashboard/dashboard_web/components/decision/DecisionAnalysis.tsx
services/dashboard/dashboard_web/components/decision/DecisionComparison.tsx
services/dashboard/dashboard_web/components/decision/DecisionConfigEditor.tsx
services/dashboard/dashboard_web/components/decision/DecisionHeatmap.tsx
services/dashboard/dashboard_web/components/decision/DecisionQualityKPI.tsx
services/dashboard/dashboard_web/components/decision/DecisionQueue.tsx
services/dashboard/dashboard_web/components/decision/DecisionTemplates.tsx
services/dashboard/dashboard_web/components/decision/EveningRotationPlan.tsx
services/dashboard/dashboard_web/components/decision/FactorAnalysis.tsx
services/dashboard/dashboard_web/components/decision/FuturesResearchPanel.tsx
services/dashboard/dashboard_web/components/decision/IntradaySignal.tsx
services/dashboard/dashboard_web/components/decision/KeyboardShortcutsHelp.tsx
services/dashboard/dashboard_web/components/decision/OptimizerPanel.tsx
services/dashboard/dashboard_web/components/decision/ParamInput.tsx
services/dashboard/dashboard_web/components/decision/ParameterOptimizer.tsx
services/dashboard/dashboard_web/components/decision/PerformanceKPI.tsx
services/dashboard/dashboard_web/components/decision/PostMarketReport.tsx
services/dashboard/dashboard_web/components/decision/ProgressTracker.tsx
services/dashboard/dashboard_web/components/decision/ReportViewer.tsx
services/dashboard/dashboard_web/components/decision/SignalDistributionChart.tsx
services/dashboard/dashboard_web/components/decision/StockPoolTable.tsx
services/dashboard/dashboard_web/components/decision/StrategyImport.tsx
services/dashboard/dashboard_web/components/decision/panel/config-runtime.tsx
services/dashboard/dashboard_web/components/decision/panel/models-factors.tsx
services/dashboard/dashboard_web/components/decision/panel/notifications-report.tsx
services/dashboard/dashboard_web/components/decision/panel/overview.tsx
services/dashboard/dashboard_web/components/decision/panel/research-center.tsx
services/dashboard/dashboard_web/components/decision/panel/signal-review.tsx
services/dashboard/dashboard_web/components/decision/panel/strategy-repository.tsx
```

### 数据业务组件（20 个）
```
services/dashboard/dashboard_web/components/data/CollectionAnalysis.tsx
services/dashboard/dashboard_web/components/data/CollectionHeatmap.tsx
services/dashboard/dashboard_web/components/data/CollectionOptimizer.tsx
services/dashboard/dashboard_web/components/data/CollectionQueue.tsx
services/dashboard/dashboard_web/components/data/CollectionStatsChart.tsx
services/dashboard/dashboard_web/components/data/DataQualityKPI.tsx
services/dashboard/dashboard_web/components/data/DataSourceAnalysis.tsx
services/dashboard/dashboard_web/components/data/DataSourceComparison.tsx
services/dashboard/dashboard_web/components/data/DataSourceConfigEditor.tsx
services/dashboard/dashboard_web/components/data/DataSourceHealthKPI.tsx
services/dashboard/dashboard_web/components/data/DataSourceTemplates.tsx
services/dashboard/dashboard_web/components/data/KeyboardShortcutsHelp.tsx
services/dashboard/dashboard_web/components/data/ProgressTracker.tsx
services/dashboard/dashboard_web/components/data/SourceConfigInput.tsx
services/dashboard/dashboard_web/components/data/pages/collectors-page.tsx
services/dashboard/dashboard_web/components/data/pages/data-explorer-page.tsx
services/dashboard/dashboard_web/components/data/pages/news-feed-page.tsx
services/dashboard/dashboard_web/components/data/pages/overview-page.tsx
services/dashboard/dashboard_web/components/data/pages/settings-page.tsx
services/dashboard/dashboard_web/components/data/pages/system-monitor-page.tsx
```

### Hooks（2 个）
```
services/dashboard/dashboard_web/hooks/use-mobile.ts
services/dashboard/dashboard_web/hooks/use-toast.ts
```

### Lib / API（9 个）
```
services/dashboard/dashboard_web/lib/sim-api.ts
services/dashboard/dashboard_web/lib/backtest-api.ts
services/dashboard/dashboard_web/lib/decision-api.ts
services/dashboard/dashboard_web/lib/data-api.ts
services/dashboard/dashboard_web/lib/audio.ts
services/dashboard/dashboard_web/lib/keyboard.ts
services/dashboard/dashboard_web/lib/notification.ts
services/dashboard/dashboard_web/lib/contracts.ts
services/dashboard/dashboard_web/lib/collector-labels.ts
```
