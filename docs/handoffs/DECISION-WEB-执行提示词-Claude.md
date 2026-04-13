# Claude Code 执行提示词 — 决策端看板全面增强

---

## 🎯 任务概述

你需要完成 **decision 服务看板**的全面增强，参考 **backtest 看板**的成功经验（BACKTEST-WEB-01/02/03 已 100% 完成）。

**重要**：Jay.S 已确认所有 Token 已签发（或即将签发），可以直接开始实施，无需等待审批。

---

## 📋 执行前必读

### 1. 阅读以下文档（按顺序）

1. `/Users/jayshao/JBT/docs/handoffs/DECISION-WEB-Token申请-Atlas.md`（任务规划）
2. `/Users/jayshao/JBT/docs/handoffs/BACKTEST-WEB-最终完成报告-Claude.md`（参考案例）
3. `/Users/jayshao/JBT/CLAUDE.md`（JBT 治理规则）

### 2. 确认当前状态

- 当前分支：main
- 工作目录：`/Users/jayshao/JBT`
- Token 状态：已签发（或待签发，Jay.S 确认）
- 任务编号：DECISION-WEB-01/02/03

---

## 🚀 执行计划

### 阶段 1：第一阶段（P0+P1）— 10项功能

#### P0-1：决策历史持久化（2小时）

**后端**：
1. 修改 `services/decision/src/api/app.py`
   - 新增 `GET /api/v1/decision/history` 端点
   - 支持 `start_date` 和 `end_date` 查询参数

**前端**：
1. 创建 `services/decision/decision_web/lib/decision-api.ts`
   - 新增 `decisionHistory(startDate, endDate)` 方法

2. 创建 `services/decision/decision_web/app/history/page.tsx`
   - 从后端获取历史数据，显示决策结果列表

**验收**：决策历史列表可以查看和筛选

---

#### P0-2：策略参数实时验证（2小时）

**后端**：
1. 新建 `services/decision/src/decision/validator.py`
   - 实现 `ParameterValidator` 类
   - 方法：`validate_type()`, `validate_range()`, `validate_dependencies()`

2. 修改 `services/decision/src/api/app.py`
   - 新增 `POST /api/v1/strategy/validate` 端点

**前端**：
1. 创建 `services/decision/decision_web/components/ParamInput.tsx`
   - 参数输入框添加实时验证
   - 显示验证错误信息

**验收**：策略参数输入有实时验证反馈

---

#### P0-3：决策进度实时推送（3小时）

**后端**：
1. 修改 `services/decision/src/api/app.py`
   - 新增 `GET /api/v1/decision/progress/{id}/stream` 端点（SSE）
   - 推送进度百分比、当前阶段、预计完成时间

**前端**：
1. 创建 `services/decision/decision_web/components/ProgressTracker.tsx`
   - 添加进度条组件
   - 使用 EventSource 接收 SSE 推送

**验收**：决策进度实时显示（进度条 + 百分比）

---

#### P1-1：决策绩效 KPI（3小时）

**后端**：
1. 新建 `services/decision/src/stats/__init__.py`
2. 新建 `services/decision/src/stats/performance.py`
   - 实现 `PerformanceCalculator` 类
   - 方法：`calculate_signal_accuracy()`, `calculate_avg_return()`, `calculate_max_drawdown()`, `calculate_sharpe_ratio()`, `calculate_signal_count()`, `calculate_execution_success_rate()`, `calculate_avg_response_time()`

3. 修改 `services/decision/src/api/app.py`
   - 新增 `GET /api/v1/decision/{id}/performance` 端点

**前端**：
1. 创建 `services/decision/decision_web/components/PerformanceKPI.tsx`
   - 展示 7 个 KPI：信号准确率、平均收益率、最大回撤、夏普比率、信号数量、执行成功率、平均响应时间

2. 修改 `services/decision/decision_web/app/decisions/page.tsx`
   - 集成 PerformanceKPI 组件

**验收**：绩效 KPI 显示 7 个指标

---

#### P1-2：决策质量 KPI（3小时）

**后端**：
1. 新建 `services/decision/src/stats/quality.py`
   - 实现 `QualityCalculator` 类
   - 方法：`calculate_signal_quality()`, `calculate_factor_effectiveness()`, `calculate_strategy_stability()`, `calculate_risk_control_effectiveness()`, `calculate_data_completeness()`

2. 修改 `services/decision/src/api/app.py`
   - 新增 `GET /api/v1/decision/{id}/quality` 端点

**前端**：
1. 创建 `services/decision/decision_web/components/DecisionQualityKPI.tsx`
   - 展示 5 个 KPI：信号质量评分、因子有效性、策略稳定性、风险控制有效性、数据完整性

2. 修改 `services/decision/decision_web/app/decisions/page.tsx`
   - 集成 DecisionQualityKPI 组件

**验收**：质量 KPI 显示 5 个指标

---

#### P1-3：批量决策功能（3小时）

**后端**：
1. 修改 `services/decision/src/api/app.py`
   - 新增 `POST /api/v1/decision/batch` 端点
   - 支持参数网格搜索

**前端**：
1. 修改 `services/decision/decision_web/app/decisions/page.tsx`
   - 添加批量决策配置界面
   - 参数网格输入（起始值/结束值/步长）

**验收**：支持批量决策（参数网格）

---

#### P1-4：决策结果对比（3小时）

**前端**：
1. 创建 `services/decision/decision_web/components/DecisionComparison.tsx`
   - 支持选择多个决策结果
   - 并排显示绩效指标
   - 并排显示信号分布

2. 修改 `services/decision/decision_web/app/decisions/page.tsx`
   - 添加"对比"按钮
   - 集成 DecisionComparison 组件

**验收**：支持多个决策结果对比

---

#### P1-5：实时决策告警（2小时）

**前端**：
1. 创建 `services/decision/decision_web/lib/notification.ts`
   - 实现 `requestNotificationPermission()` 和 `showNotification()` 方法

2. 创建 `services/decision/decision_web/lib/audio.ts`
   - 实现 `initAudio()` 和 `playAlertSound()` 方法

3. 修改 `services/decision/decision_web/app/decisions/page.tsx`
   - 集成浏览器通知和音频告警

**验收**：决策完成有浏览器通知和音频告警

---

#### P1-6：信号分布可视化（4小时）

**前端**：
1. 创建 `services/decision/decision_web/components/SignalDistributionChart.tsx`
   - 使用 recharts 绘制信号时间分布图
   - 绘制信号类型分布图
   - 支持缩放和拖拽

2. 修改 `services/decision/decision_web/app/decisions/page.tsx`
   - 集成 SignalDistributionChart 组件

**验收**：信号分布图表完整

---

#### P1-7：因子分析详情（3小时）

**前端**：
1. 创建 `services/decision/decision_web/components/FactorAnalysis.tsx`
   - 因子列表（支持按贡献度/相关性排序）
   - 因子统计（有效性/稳定性/覆盖率）
   - 因子筛选（按类型/有效性）

2. 修改 `services/decision/decision_web/app/decisions/page.tsx`
   - 集成 FactorAnalysis 组件

**验收**：因子分析可以查看和排序

---

### 阶段 2：第二阶段（P2）— 6项功能

#### P2-1：决策结果分析增强（4小时）

**前端**：
1. 创建 `services/decision/decision_web/components/DecisionAnalysis.tsx`
   - 月度信号热力图
   - 年度收益对比
   - 分品种绩效分析

**验收**：月度信号热力图显示正常

---

#### P2-2：策略参数优化器（5小时）

**后端**：
1. 创建 `services/decision/src/stats/optimizer.py`
   - 实现 `ParameterOptimizer` 类
   - 方法：`grid_search()`, `genetic_algorithm()`, `bayesian_optimization()`

2. 修改 `services/decision/src/api/app.py`
   - 新增 `POST /api/v1/optimize/grid` 端点

**前端**：
1. 创建 `services/decision/decision_web/components/ParameterOptimizer.tsx`
   - 参数网格搜索界面
   - 优化结果展示

2. 创建 `services/decision/decision_web/app/optimizer/page.tsx`
   - 集成 ParameterOptimizer 组件

**验收**：参数优化器支持网格搜索

---

#### P2-3：决策配置可视化编辑（3小时）

**前端**：
1. 创建 `services/decision/decision_web/components/DecisionConfigEditor.tsx`
   - 策略参数编辑器
   - 因子权重配置
   - 风控参数配置

**验收**：决策配置编辑器可以修改并保存

---

#### P2-4：决策任务队列管理（4小时）

**后端**：
1. 创建 `services/decision/src/queue/__init__.py`
2. 创建 `services/decision/src/queue/manager.py`
   - 实现 `QueueManager` 类
   - 方法：`add_task()`, `get_queue()`, `cancel_task()`, `retry_task()`

3. 修改 `services/decision/src/api/app.py`
   - 新增 `GET /api/v1/decision/queue` 端点

**前端**：
1. 创建 `services/decision/decision_web/components/DecisionQueue.tsx`
   - 任务列表（待执行/执行中/已完成）
   - 任务操作（取消/重试/调整优先级）

**验收**：任务队列可以查看和管理

---

#### P2-5：决策模板功能（3小时）

**前端**：
1. 创建 `services/decision/decision_web/components/DecisionTemplates.tsx`
   - 预设模板（趋势/反转/套利）
   - 自定义模板保存
   - 模板导入导出

**验收**：模板可以保存、加载和导入导出

---

#### P2-6：多时间框架分析（2小时）

**前端**：
1. 修改 `services/decision/decision_web/app/decisions/page.tsx`
   - 添加时间框架切换按钮
   - 支持多个时间周期对比

**验收**：多时间框架分析正常工作

---

### 阶段 3：第三阶段（P3）— 3项功能

#### P3-1：键盘快捷键系统（2小时）

**前端**：
1. 创建 `services/decision/decision_web/lib/keyboard.ts`
   - 实现全局快捷键管理
   - 8个快捷键：开始决策/停止决策/查看结果/参数优化/刷新数据/切换主题/聚焦搜索/帮助

2. 创建 `services/decision/decision_web/components/KeyboardShortcutsHelp.tsx`
   - 快捷键帮助面板

**验收**：键盘快捷键系统正常工作

---

#### P3-2：主题切换（1小时）

**前端**：
1. 创建 `services/decision/decision_web/components/ThemeToggle.tsx`
   - 暗色/亮色模式切换
   - 主题持久化

**验收**：主题切换功能正常

---

#### P3-3：决策热力图（3小时）

**前端**：
1. 创建 `services/decision/decision_web/components/DecisionHeatmap.tsx`
   - 参数热力图（参数组合 vs 收益率）
   - 时间热力图（月度信号分布）

**验收**：决策热力图显示正常

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
git commit -m "feat(decision): DECISION-WEB-01 P0-1 决策历史持久化"
```

Commit 消息格式：
- `feat(decision): DECISION-WEB-01 <功能编号> <功能描述>`
- 例如：`feat(decision): DECISION-WEB-01 P1-3 批量决策功能`

### 3. 测试规范

每完成一个后端功能，编写单元测试：

```python
# services/decision/tests/test_stats.py
def test_calculate_signal_accuracy():
    calculator = PerformanceCalculator()
    signals = [...]
    accuracy = calculator.calculate_signal_accuracy(signals)
    assert accuracy > 0
```

### 4. 验收规范

每完成一个功能，立即验收：
1. 后端：运行单元测试 `pytest services/decision/tests/`
2. 前端：运行构建 `cd services/decision/decision_web && pnpm build`
3. 集成：启动服务，手动测试功能

---

## 🎯 执行顺序

### 第 1-2 天（16小时）
- P0-1：决策历史持久化（2h）
- P0-2：策略参数实时验证（2h）
- P0-3：决策进度实时推送（3h）
- P1-1：决策绩效 KPI（3h）
- P1-2：决策质量 KPI（3h）
- P1-3：批量决策功能（3h）

### 第 3 天（8小时）
- P1-4：决策结果对比（3h）
- P1-5：实时决策告警（2h）
- P1-6：信号分布可视化（4h）

### 第 4 天（8小时）
- P1-7：因子分析详情（3h）
- 验收第一阶段（2h）
- P2-1：决策结果分析增强（4h）

### 第 5 天（8小时）
- P2-2：策略参数优化器（5h）
- P2-3：决策配置可视化编辑（3h）

### 第 6 天（8小时）
- P2-4：决策任务队列管理（4h）
- P2-5：决策模板功能（3h）
- P2-6：多时间框架分析（2h）

### 第 7 天（6小时）
- P3-1：键盘快捷键系统（2h）
- P3-2：主题切换（1h）
- P3-3：决策热力图（3h）
- 最终验收（1h）

---

## 📦 可复用代码（从 backtest）

以下组件可以直接复用或稍作修改：

1. **ThemeToggle.tsx** - 主题切换（完全复用）
2. **keyboard.ts** - 快捷键管理（修改快捷键定义）
3. **notification.ts** - 浏览器通知（完全复用）
4. **audio.ts** - 音频告警（完全复用）
5. **PerformanceKPI.tsx** - 绩效 KPI（修改指标）
6. **ProgressTracker.tsx** - 进度追踪（完全复用）
7. **ParamInput.tsx** - 参数输入（完全复用）

复用方式：
```bash
# 复制文件
cp services/backtest/backtest_web/components/ThemeToggle.tsx \
   services/decision/decision_web/components/ThemeToggle.tsx

# 修改导入路径和组件名称
```

---

## ⚠️ 注意事项

1. **不要修改白名单以外的文件**
2. **每个功能独立 commit**
3. **遇到问题立即停止，向用户汇报**
4. **保持代码风格与现有代码一致**
5. **所有 API 端点都要添加到 `decision-api.ts`**
6. **前端组件使用 shadcn/ui 风格**
7. **图表使用 recharts 库**
8. **参考 backtest 的实现，但不要照搬（decision 有自己的特点）**

---

## 📊 完成后汇报

完成所有功能后，汇报：

1. **Commit 列表**（每个功能的 commit hash）
2. **测试结果**（单元测试通过数量）
3. **构建结果**（前端构建是否成功）
4. **遇到的问题**（如果有）
5. **建议的优化方向**（如果有）

生成完成报告：`docs/handoffs/DECISION-WEB-完成报告-Claude.md`

---

## 🚀 开始执行

现在开始执行 DECISION-WEB-01/02/03 任务，从 P0-1 开始。

**第一步**：读取 `services/decision/src/api/app.py` 文件，了解当前代码结构。

祝执行顺利！🚀

---

**创建时间**：2026-04-13  
**执行人**：Claude Code（新窗口）  
**参考任务**：BACKTEST-WEB-01/02/03（已 100% 完成）  
**参考报告**：`docs/handoffs/BACKTEST-WEB-最终完成报告-Claude.md`
