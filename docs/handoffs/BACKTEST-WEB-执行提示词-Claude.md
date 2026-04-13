# Claude Code 执行提示词 — 回测端看板全面增强

---

## 🎯 任务概述

你需要完成 backtest 服务看板的全面增强，参考 sim-trading 看板的成功经验（SIMWEB-01/02/03 已 100% 完成）。

**重要**：Jay.S 已确认所有 Token 已签发，可以直接开始实施，无需等待审批。

---

## 📋 执行前必读

### 1. 阅读以下文档（按顺序）

1. `/Users/jayshao/JBT/docs/handoffs/BACKTEST-WEB-Token申请-Claude.md`（任务规划）
2. `/Users/jayshao/JBT/services/sim-trading/参考文档/SIMWEB-01-模拟交易看板全面增强-第一阶段.md`（参考案例）
3. `/Users/jayshao/JBT/docs/handoffs/SIMWEB-02-03-完成报告-Claude.md`（参考案例）
4. `/Users/jayshao/JBT/CLAUDE.md`（JBT 治理规则）

### 2. 确认当前状态

- 当前分支：main
- 工作目录：`/Users/jayshao/JBT`
- Token 状态：已签发（Jay.S 确认）
- 任务编号：BACKTEST-WEB-01/02/03

---

## 🚀 执行计划

### 阶段 1：第一阶段（P0+P1）— 10项功能

#### P0-1：回测结果历史持久化（2小时）

**后端**：
1. 修改 `services/backtest/src/backtest/service.py`
   - 新增 `backtest_history: List[dict]` 属性
   - 新增 `save_backtest_result(result)` 方法
   - 新增 `get_backtest_history(start_date, end_date)` 方法

2. 修改 `services/backtest/src/api/app.py`
   - 新增 `GET /api/v1/backtest/history` 端点
   - 支持 `start_date` 和 `end_date` 查询参数

**前端**：
1. 修改 `services/backtest/backtest_web/lib/backtest-api.ts`
   - 新增 `backtestHistory(startDate, endDate)` 方法

2. 修改 `services/backtest/backtest_web/app/results/page.tsx`
   - 从后端获取历史数据，显示回测结果列表

**验收**：回测历史列表可以查看和筛选

---

#### P0-2：策略参数实时验证（2小时）

**后端**：
1. 新建 `services/backtest/src/backtest/validator.py`
   - 实现 `ParameterValidator` 类
   - 方法：`validate_type()`, `validate_range()`, `validate_dependencies()`

2. 修改 `services/backtest/src/api/app.py`
   - 新增 `POST /api/v1/strategy/validate` 端点

**前端**：
1. 修改 `services/backtest/backtest_web/app/backtest/page.tsx`
   - 参数输入框添加实时验证
   - 显示验证错误信息

**验收**：策略参数输入有实时验证反馈

---

#### P0-3：回测进度实时推送（3小时）

**后端**：
1. 修改 `services/backtest/src/api/app.py`
   - 新增 `GET /api/v1/backtest/progress` 端点（SSE）
   - 推送进度百分比、当前日期、预计完成时间

**前端**：
1. 修改 `services/backtest/backtest_web/app/backtest/page.tsx`
   - 添加进度条组件
   - 使用 EventSource 接收 SSE 推送

**验收**：回测进度实时显示（进度条 + 百分比）

---

#### P1-1：回测绩效 KPI（3小时）

**后端**：
1. 新建 `services/backtest/src/stats/__init__.py`
2. 新建 `services/backtest/src/stats/performance.py`
   - 实现 `PerformanceCalculator` 类
   - 方法：`calculate_annual_return()`, `calculate_max_drawdown()`, `calculate_sharpe_ratio()`, `calculate_calmar_ratio()`, `calculate_win_rate()`, `calculate_profit_loss_ratio()`, `calculate_total_trades()`

3. 修改 `services/backtest/src/api/app.py`
   - 新增 `GET /api/v1/backtest/{id}/performance` 端点

**前端**：
1. 新建 `services/backtest/backtest_web/components/PerformanceKPI.tsx`
   - 展示 7 个 KPI：年化收益率、最大回撤、夏普比率、卡玛比率、胜率、盈亏比、总交易次数

2. 修改 `services/backtest/backtest_web/app/results/page.tsx`
   - 集成 PerformanceKPI 组件

**验收**：绩效 KPI 显示 7 个指标

---

#### P1-2：回测质量 KPI（3小时）

**后端**：
1. 新建 `services/backtest/src/stats/quality.py`
   - 实现 `QualityCalculator` 类
   - 方法：`calculate_out_of_sample_performance()`, `detect_overfitting()`, `calculate_stability_score()`, `calculate_parameter_sensitivity()`, `calculate_data_quality_score()`

2. 修改 `services/backtest/src/api/app.py`
   - 新增 `GET /api/v1/backtest/{id}/quality` 端点

**前端**：
1. 新建 `services/backtest/backtest_web/components/BacktestQualityKPI.tsx`
   - 展示 5 个 KPI：样本外表现、过拟合检测、稳定性评分、参数敏感度、数据质量评分

2. 修改 `services/backtest/backtest_web/app/results/page.tsx`
   - 集成 BacktestQualityKPI 组件

**验收**：质量 KPI 显示 5 个指标

---

#### P1-3：批量回测功能（3小时）

**后端**：
1. 修改 `services/backtest/src/api/app.py`
   - 新增 `POST /api/v1/backtest/batch` 端点
   - 支持参数网格搜索

**前端**：
1. 修改 `services/backtest/backtest_web/app/backtest/page.tsx`
   - 添加批量回测配置界面
   - 参数网格输入（起始值/结束值/步长）

**验收**：支持批量回测（参数网格）

---

#### P1-4：回测结果对比（3小时）

**前端**：
1. 新建 `services/backtest/backtest_web/components/BacktestComparison.tsx`
   - 支持选择多个回测结果
   - 并排显示绩效指标
   - 并排显示权益曲线

2. 修改 `services/backtest/backtest_web/app/results/page.tsx`
   - 添加"对比"按钮
   - 集成 BacktestComparison 组件

**验收**：支持多个回测结果对比

---

#### P1-5：实时回测告警（2小时）

**后端**：
1. 修改 `services/backtest/src/api/app.py`
   - 新增 `GET /api/v1/backtest/alerts` 端点（SSE）

**前端**：
1. 新建 `services/backtest/backtest_web/lib/notification.ts`
   - 实现 `requestNotificationPermission()` 和 `showNotification()` 方法

2. 新建 `services/backtest/backtest_web/lib/audio.ts`
   - 实现 `initAudio()` 和 `playAlertSound()` 方法

3. 新增 `services/backtest/backtest_web/public/alert.mp3`
   - 告警音频文件（占位符）

4. 修改 `services/backtest/backtest_web/app/backtest/page.tsx`
   - 集成浏览器通知和音频告警

**验收**：回测完成有浏览器通知和音频告警

---

#### P1-6：权益曲线技术分析（4小时）

**前端**：
1. 新建 `services/backtest/backtest_web/components/EquityCurveChart.tsx`
   - 使用 recharts 绘制权益曲线
   - 绘制回撤曲线
   - 绘制水下曲线（underwater curve）
   - 支持缩放和拖拽

2. 修改 `services/backtest/backtest_web/app/results/page.tsx`
   - 集成 EquityCurveChart 组件

**验收**：权益曲线图表完整（权益/回撤/水下）

---

#### P1-7：交易明细分析（3小时）

**前端**：
1. 新建 `services/backtest/backtest_web/components/TradeDetailAnalysis.tsx`
   - 交易列表（支持按盈亏/时间/品种排序）
   - 交易统计（胜率/盈亏比/平均持仓时间）
   - 交易筛选（按品种/方向/盈亏状态）

2. 修改 `services/backtest/backtest_web/app/results/page.tsx`
   - 集成 TradeDetailAnalysis 组件

**验收**：交易明细可以查看和排序

---

### 阶段 2：第二阶段（P2）— 6项功能

#### P2-1：回测结果分析增强（4小时）

**前端**：
1. 新建 `services/backtest/backtest_web/components/BacktestAnalysis.tsx`
   - 月度收益热力图
   - 年度收益对比
   - 分品种绩效分析

**验收**：月度收益热力图显示正常

---

#### P2-2：策略参数优化器（5小时）

**后端**：
1. 新建 `services/backtest/src/stats/optimizer.py`
   - 实现 `ParameterOptimizer` 类
   - 方法：`grid_search()`, `genetic_algorithm()`, `bayesian_optimization()`

2. 修改 `services/backtest/src/api/app.py`
   - 新增 `POST /api/v1/optimize/grid` 端点

**前端**：
1. 新建 `services/backtest/backtest_web/components/ParameterOptimizer.tsx`
   - 参数网格搜索界面
   - 优化结果展示

2. 修改 `services/backtest/backtest_web/app/optimizer/page.tsx`
   - 集成 ParameterOptimizer 组件

**验收**：参数优化器支持网格搜索

---

#### P2-3：回测配置可视化编辑（3小时）

**前端**：
1. 新建 `services/backtest/backtest_web/components/BacktestConfigEditor.tsx`
   - 回测时间范围选择器
   - 初始资金配置
   - 手续费/滑点配置

**验收**：回测配置编辑器可以修改并保存

---

#### P2-4：回测任务队列管理（4小时）

**后端**：
1. 新建 `services/backtest/src/queue/__init__.py`
2. 新建 `services/backtest/src/queue/manager.py`
   - 实现 `QueueManager` 类
   - 方法：`add_task()`, `get_queue()`, `cancel_task()`, `retry_task()`

3. 修改 `services/backtest/src/api/app.py`
   - 新增 `GET /api/v1/backtest/queue` 端点

**前端**：
1. 新建 `services/backtest/backtest_web/components/BacktestQueue.tsx`
   - 任务列表（待执行/执行中/已完成）
   - 任务操作（取消/重试/调整优先级）

**验收**：任务队列可以查看和管理

---

#### P2-5：回测模板功能（3小时）

**前端**：
1. 新建 `services/backtest/backtest_web/components/BacktestTemplates.tsx`
   - 预设模板（日内/趋势/套利）
   - 自定义模板保存
   - 模板导入导出

**验收**：模板可以保存、加载和导入导出

---

#### P2-6：多时间框架分析（2小时）

**前端**：
1. 修改 `services/backtest/backtest_web/app/results/page.tsx`
   - 添加时间框架切换按钮
   - 支持多个时间周期对比

**验收**：多时间框架分析正常工作

---

### 阶段 3：第三阶段（P3）— 3项功能

#### P3-1：键盘快捷键系统（2小时）

**前端**：
1. 新建 `services/backtest/backtest_web/lib/keyboard.ts`
   - 实现全局快捷键管理
   - 8个快捷键：开始回测/停止回测/查看结果/参数优化/刷新数据/切换主题/聚焦搜索/帮助

2. 新建 `services/backtest/backtest_web/components/KeyboardShortcutsHelp.tsx`
   - 快捷键帮助面板

**验收**：键盘快捷键系统正常工作

---

#### P3-2：主题切换（1小时）

**前端**：
1. 新建 `services/backtest/backtest_web/components/ThemeToggle.tsx`
   - 暗色/亮色模式切换
   - 主题持久化

**验收**：主题切换功能正常

---

#### P3-3：回测热力图（3小时）

**前端**：
1. 新建 `services/backtest/backtest_web/components/BacktestHeatmap.tsx`
   - 参数热力图（参数组合 vs 收益率）
   - 时间热力图（月度收益分布）

**验收**：回测热力图显示正常

---

## 📝 执行规范

### 1. 代码规范

- **Python 3.9 兼容**：使用 `Optional[str]` 而非 `str | None`
- **类型注解**：所有函数都要有类型注解
- **错误处理**：使用 try-except 捕获异常
- **日志记录**：使用 `logging.getLogger(__name__)`

### 2. Commit 规范

每完成一个功能，立即 commit：

```bash
git add <files>
git commit -m "feat(backtest): BACKTEST-WEB-01 P0-1 回测结果历史持久化"
```

Commit 消息格式：
- `feat(backtest): BACKTEST-WEB-01 <功能编号> <功能描述>`
- 例如：`feat(backtest): BACKTEST-WEB-01 P1-3 批量回测功能`

### 3. 测试规范

每完成一个后端功能，编写单元测试：

```python
# services/backtest/tests/test_stats.py
def test_calculate_annual_return():
    calculator = PerformanceCalculator()
    trades = [...]
    annual_return = calculator.calculate_annual_return(trades)
    assert annual_return > 0
```

### 4. 验收规范

每完成一个功能，立即验收：
1. 后端：运行单元测试 `pytest services/backtest/tests/`
2. 前端：运行构建 `cd services/backtest/backtest_web && pnpm build`
3. 集成：启动服务，手动测试功能

---

## 🎯 执行顺序

### 第 1-2 天（16小时）
- P0-1：回测结果历史持久化（2h）
- P0-2：策略参数实时验证（2h）
- P0-3：回测进度实时推送（3h）
- P1-1：回测绩效 KPI（3h）
- P1-2：回测质量 KPI（3h）
- P1-3：批量回测功能（3h）

### 第 3 天（8小时）
- P1-4：回测结果对比（3h）
- P1-5：实时回测告警（2h）
- P1-6：权益曲线技术分析（4h）

### 第 4 天（8小时）
- P1-7：交易明细分析（3h）
- 验收第一阶段（2h）
- P2-1：回测结果分析增强（4h）

### 第 5 天（8小时）
- P2-2：策略参数优化器（5h）
- P2-3：回测配置可视化编辑（3h）

### 第 6 天（8小时）
- P2-4：回测任务队列管理（4h）
- P2-5：回测模板功能（3h）
- P2-6：多时间框架分析（2h）

### 第 7 天（6小时）
- P3-1：键盘快捷键系统（2h）
- P3-2：主题切换（1h）
- P3-3：回测热力图（3h）
- 最终验收（1h）

---

## 📦 可复用代码（从 sim-trading）

以下组件可以直接复用或稍作修改：

1. **ThemeToggle.tsx** - 主题切换（完全复用）
2. **keyboard.ts** - 快捷键管理（修改快捷键定义）
3. **notification.ts** - 浏览器通知（完全复用）
4. **audio.ts** - 音频告警（完全复用）
5. **PerformanceKPI.tsx** - 绩效 KPI（修改指标）

复用方式：
```bash
# 复制文件
cp services/sim-trading/sim-trading_web/components/ThemeToggle.tsx \
   services/backtest/backtest_web/components/ThemeToggle.tsx

# 修改导入路径和组件名称
```

---

## ⚠️ 注意事项

1. **不要修改白名单以外的文件**
2. **每个功能独立 commit**
3. **遇到问题立即停止，向用户汇报**
4. **保持代码风格与现有代码一致**
5. **所有 API 端点都要添加到 `backtest-api.ts`**
6. **前端组件使用 shadcn/ui 风格**
7. **图表使用 recharts 库**
8. **参考 sim-trading 的实现，但不要照搬（回测有自己的特点）**

---

## 📊 完成后汇报

完成所有功能后，汇报：

1. **Commit 列表**（每个功能的 commit hash）
2. **测试结果**（单元测试通过数量）
3. **构建结果**（前端构建是否成功）
4. **遇到的问题**（如果有）
5. **建议的优化方向**（如果有）

生成完成报告：`docs/handoffs/BACKTEST-WEB-完成报告-Claude.md`

---

## 🚀 开始执行

现在开始执行 BACKTEST-WEB-01/02/03 任务，从 P0-1 开始。

**第一步**：读取 `services/backtest/src/backtest/service.py` 文件，了解当前代码结构。

祝执行顺利！🚀

---

**创建时间**：2026-04-13  
**执行人**：Claude Code  
**参考任务**：SIMWEB-01/02/03（已 100% 完成）
