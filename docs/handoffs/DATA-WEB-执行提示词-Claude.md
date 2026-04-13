# Claude Code 执行提示词 — 数据端看板全面增强

---

## 🎯 任务概述

你需要完成 **data 服务看板**的全面增强，参考 **backtest 看板**和 **decision 看板**的成功经验（均已 100% 完成）。

**重要**：Jay.S 已确认所有 Token 已签发（或即将签发），可以直接开始实施，无需等待审批。

---

## 📋 执行前必读

### 1. 阅读以下文档（按顺序）

1. `/Users/jayshao/JBT/docs/handoffs/DATA-WEB-Token申请-Atlas.md`（任务规划）
2. `/Users/jayshao/JBT/docs/handoffs/DECISION-WEB-完成报告-Claude.md`（参考案例）
3. `/Users/jayshao/JBT/CLAUDE.md`（JBT 治理规则）

### 2. 确认当前状态

- 当前分支：main
- 工作目录：`/Users/jayshao/JBT`
- Token 状态：已签发（或待签发，Jay.S 确认）
- 任务编号：DATA-WEB-01/02/03

---

## 🚀 执行计划

### 阶段 1：第一阶段（P0+P1）— 10项功能

#### P0-1：数据采集历史记录（2小时）

**后端**：
1. 修改 `services/data/src/api/app.py`
   - 新增 `GET /api/v1/data/collection/history` 端点
   - 支持 `start_date`、`end_date`、`source` 查询参数

**前端**：
1. 创建 `services/data/data_web/lib/data-api.ts`
   - 新增 `collectionHistory(startDate, endDate, source)` 方法

2. 创建 `services/data/data_web/app/history/page.tsx`
   - 从后端获取历史数据，显示采集记录列表

**验收**：采集历史列表可以查看和筛选

---

#### P0-2：数据源配置验证（2小时）

**后端**：
1. 新建 `services/data/src/data/validator.py`
   - 实现 `DataSourceValidator` 类
   - 方法：`validate_connection()`, `validate_config()`, `validate_permissions()`

2. 修改 `services/data/src/api/app.py`
   - 新增 `POST /api/v1/data/source/validate` 端点

**前端**：
1. 创建 `services/data/data_web/components/SourceConfigInput.tsx`
   - 数据源配置输入框添加实时验证
   - 显示验证错误信息

**验收**：数据源配置有实时验证反馈

---

#### P0-3：采集进度实时推送（3小时）

**后端**：
1. 新建 `services/data/src/data/progress_tracker.py`
   - 实现 `ProgressTracker` 类（复用 decision 的实现）

2. 修改 `services/data/src/api/app.py`
   - 新增 `GET /api/v1/data/collection/progress/{id}/stream` 端点（SSE）
   - 推送进度百分比、当前阶段、预计完成时间

**前端**：
1. 创建 `services/data/data_web/components/ProgressTracker.tsx`
   - 添加进度条组件（复用 decision 的实现）
   - 使用 EventSource 接收 SSE 推送

**验收**：采集进度实时显示（进度条 + 百分比）

---

#### P1-1：数据质量 KPI（3小时）

**后端**：
1. 新建 `services/data/src/stats/__init__.py`
2. 新建 `services/data/src/stats/quality.py`
   - 实现 `DataQualityCalculator` 类
   - 方法：`calculate_completeness()`, `calculate_timeliness()`, `calculate_accuracy()`, `calculate_consistency()`, `calculate_success_rate()`, `calculate_avg_latency()`, `calculate_error_rate()`

3. 修改 `services/data/src/api/app.py`
   - 新增 `GET /api/v1/data/collection/{id}/quality` 端点

**前端**：
1. 创建 `services/data/data_web/components/DataQualityKPI.tsx`
   - 展示 7 个 KPI：数据完整性、及时性、准确性、一致性、采集成功率、平均延迟、错误率

2. 修改 `services/data/data_web/app/collections/page.tsx`
   - 集成 DataQualityKPI 组件

**验收**：数据质量 KPI 显示 7 个指标

---

#### P1-2：数据源健康 KPI（3小时）

**后端**：
1. 新建 `services/data/src/stats/health.py`
   - 实现 `DataSourceHealthCalculator` 类
   - 方法：`calculate_availability()`, `calculate_response_time()`, `calculate_error_rate()`, `calculate_freshness()`, `calculate_coverage()`

2. 修改 `services/data/src/api/app.py`
   - 新增 `GET /api/v1/data/source/{id}/health` 端点

**前端**：
1. 创建 `services/data/data_web/components/DataSourceHealthKPI.tsx`
   - 展示 5 个 KPI：可用性、响应时间、错误率、数据新鲜度、覆盖率

2. 修改 `services/data/data_web/app/collections/page.tsx`
   - 集成 DataSourceHealthKPI 组件

**验收**：数据源健康 KPI 显示 5 个指标

---

#### P1-3：批量采集任务（3小时）

**后端**：
1. 修改 `services/data/src/api/app.py`
   - 新增 `POST /api/v1/data/collection/batch` 端点
   - 支持参数网格搜索

**前端**：
1. 修改 `services/data/data_web/app/collections/page.tsx`
   - 添加批量采集配置界面
   - 参数网格输入（起始值/结束值/步长）

**验收**：支持批量采集（参数网格）

---

#### P1-4：数据源对比（3小时）

**前端**：
1. 创建 `services/data/data_web/components/DataSourceComparison.tsx`
   - 支持选择多个数据源
   - 并排显示质量指标
   - 并排显示采集统计

2. 修改 `services/data/data_web/app/collections/page.tsx`
   - 添加"对比"按钮
   - 集成 DataSourceComparison 组件

**验收**：支持多个数据源对比

---

#### P1-5：实时采集告警（2小时）

**前端**：
1. 创建 `services/data/data_web/lib/notification.ts`
   - 实现 `requestNotificationPermission()` 和 `showNotification()` 方法（复用 decision）

2. 创建 `services/data/data_web/lib/audio.ts`
   - 实现 `initAudio()` 和 `playAlertSound()` 方法（复用 decision）

3. 修改 `services/data/data_web/app/collections/page.tsx`
   - 集成浏览器通知和音频告警

**验收**：采集完成有浏览器通知和音频告警

---

#### P1-6：采集统计可视化（4小时）

**前端**：
1. 创建 `services/data/data_web/components/CollectionStatsChart.tsx`
   - 使用 recharts 绘制采集时间分布图
   - 绘制数据源分布图
   - 支持缩放和拖拽

2. 修改 `services/data/data_web/app/collections/page.tsx`
   - 集成 CollectionStatsChart 组件

**验收**：采集统计图表完整

---

#### P1-7：数据源详情分析（3小时）

**前端**：
1. 创建 `services/data/data_web/components/DataSourceAnalysis.tsx`
   - 数据源列表（支持按可用性/响应时间排序）
   - 数据源统计（成功率/延迟/覆盖率）
   - 数据源筛选（按类型/状态）

2. 修改 `services/data/data_web/app/collections/page.tsx`
   - 集成 DataSourceAnalysis 组件

**验收**：数据源分析可以查看和排序

---

### 阶段 2：第二阶段（P2）— 6项功能

#### P2-1：数据采集分析增强（4小时）

**前端**：
1. 创建 `services/data/data_web/components/CollectionAnalysis.tsx`
   - 月度采集热力图
   - 年度数据量对比
   - 分数据源绩效分析

**验收**：月度采集热力图显示正常

---

#### P2-2：采集参数优化器（5小时）

**后端**：
1. 创建 `services/data/src/stats/optimizer.py`
   - 实现 `CollectionOptimizer` 类（复用 decision 的实现）
   - 方法：`grid_search()`, `auto_tune()`, `recommend_best_practice()`

2. 修改 `services/data/src/api/app.py`
   - 新增 `POST /api/v1/data/optimize/grid` 端点

**前端**：
1. 创建 `services/data/data_web/components/CollectionOptimizer.tsx`
   - 参数网格搜索界面
   - 优化结果展示

2. 创建 `services/data/data_web/app/optimizer/page.tsx`
   - 集成 CollectionOptimizer 组件

**验收**：采集优化器支持网格搜索

---

#### P2-3：数据源配置可视化编辑（3小时）

**前端**：
1. 创建 `services/data/data_web/components/DataSourceConfigEditor.tsx`
   - 数据源参数编辑器
   - 采集频率配置
   - 重试策略配置

**验收**：数据源配置编辑器可以修改并保存

---

#### P2-4：采集任务队列管理（4小时）

**后端**：
1. 创建 `services/data/src/queue/__init__.py`
2. 创建 `services/data/src/queue/manager.py`
   - 实现 `QueueManager` 类（复用 decision 的实现）
   - 方法：`add_task()`, `get_queue()`, `cancel_task()`, `retry_task()`

3. 修改 `services/data/src/api/app.py`
   - 新增 `GET /api/v1/data/collection/queue` 端点

**前端**：
1. 创建 `services/data/data_web/components/CollectionQueue.tsx`
   - 任务列表（待执行/执行中/已完成）
   - 任务操作（取消/重试/调整优先级）

**验收**：任务队列可以查看和管理

---

#### P2-5：数据源模板功能（3小时）

**前端**：
1. 创建 `services/data/data_web/components/DataSourceTemplates.tsx`
   - 预设模板（股票/期货/宏观/新闻）
   - 自定义模板保存
   - 模板导入导出

**验收**：模板可以保存、加载和导入导出

---

#### P2-6：多时间框架分析（2小时）

**前端**：
1. 修改 `services/data/data_web/app/collections/page.tsx`
   - 添加时间框架切换按钮
   - 支持多个时间周期对比

**验收**：多时间框架分析正常工作

---

### 阶段 3：第三阶段（P3）— 3项功能

#### P3-1：键盘快捷键系统（2小时）

**前端**：
1. 创建 `services/data/data_web/lib/keyboard.ts`
   - 实现全局快捷键管理（复用 decision）
   - 8个快捷键：开始采集/停止采集/查看结果/参数优化/刷新数据/切换主题/聚焦搜索/帮助

2. 创建 `services/data/data_web/components/KeyboardShortcutsHelp.tsx`
   - 快捷键帮助面板（复用 decision）

**验收**：键盘快捷键系统正常工作

---

#### P3-2：主题切换（1小时）

**前端**：
1. 创建 `services/data/data_web/components/ThemeToggle.tsx`
   - 暗色/亮色模式切换（复用 decision）
   - 主题持久化

**验收**：主题切换功能正常

---

#### P3-3：采集热力图（3小时）

**前端**：
1. 创建 `services/data/data_web/components/CollectionHeatmap.tsx`
   - 参数热力图（参数组合 vs 成功率）
   - 时间热力图（月度采集分布）

**验收**：采集热力图显示正常

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
git commit -m "feat(data): DATA-WEB-01 P0-1 数据采集历史记录"
```

Commit 消息格式：
- `feat(data): DATA-WEB-01 <功能编号> <功能描述>`
- 例如：`feat(data): DATA-WEB-01 P1-3 批量采集任务`

### 3. 测试规范

每完成一个后端功能，编写单元测试：

```python
# services/data/tests/test_stats.py
def test_calculate_completeness():
    calculator = DataQualityCalculator()
    collections = [...]
    completeness = calculator.calculate_completeness(collections)
    assert completeness > 0
```

### 4. 验收规范

每完成一个功能，立即验收：
1. 后端：运行单元测试 `pytest services/data/tests/`
2. 前端：运行构建 `cd services/data/data_web && pnpm build`
3. 集成：启动服务，手动测试功能

---

## 🎯 执行顺序

### 第 1-2 天（16小时）
- P0-1：数据采集历史记录（2h）
- P0-2：数据源配置验证（2h）
- P0-3：采集进度实时推送（3h）
- P1-1：数据质量 KPI（3h）
- P1-2：数据源健康 KPI（3h）
- P1-3：批量采集任务（3h）

### 第 3 天（8小时）
- P1-4：数据源对比（3h）
- P1-5：实时采集告警（2h）
- P1-6：采集统计可视化（4h）

### 第 4 天（8小时）
- P1-7：数据源详情分析（3h）
- 验收第一阶段（2h）
- P2-1：数据采集分析增强（4h）

### 第 5 天（8小时）
- P2-2：采集参数优化器（5h）
- P2-3：数据源配置可视化编辑（3h）

### 第 6 天（8小时）
- P2-4：采集任务队列管理（4h）
- P2-5：数据源模板功能（3h）
- P2-6：多时间框架分析（2h）

### 第 7 天（6小时）
- P3-1：键盘快捷键系统（2h）
- P3-2：主题切换（1h）
- P3-3：采集热力图（3h）
- 最终验收（1h）

---

## 📦 可复用代码（从 decision）

以下组件可以直接复用或稍作修改：

1. **ThemeToggle.tsx** - 主题切换（完全复用）
2. **keyboard.ts** - 快捷键管理（修改快捷键定义）
3. **notification.ts** - 浏览器通知（完全复用）
4. **audio.ts** - 音频告警（完全复用）
5. **ProgressTracker.tsx** - 进度追踪（修改 API 路径）
6. **KeyboardShortcutsHelp.tsx** - 快捷键帮助（完全复用）
7. **QueueManager** - 任务队列管理（完全复用）
8. **ParameterOptimizer** - 参数优化器（修改优化目标）

复用方式：
```bash
# 复制文件
cp services/decision/decision_web/components/ThemeToggle.tsx \
   services/data/data_web/components/ThemeToggle.tsx

# 修改导入路径和组件名称
```

---

## ⚠️ 注意事项

1. **不要修改白名单以外的文件**
2. **每个功能独立 commit**
3. **遇到问题立即停止，向用户汇报**
4. **保持代码风格与现有代码一致**
5. **所有 API 端点都要添加到 `data-api.ts`**
6. **前端组件使用 shadcn/ui 风格**
7. **图表使用 recharts 库**
8. **参考 decision 的实现，但不要照搬（data 有自己的特点）**

---

## 📊 完成后汇报

完成所有功能后，汇报：

1. **Commit 列表**（每个功能的 commit hash）
2. **测试结果**（单元测试通过数量）
3. **构建结果**（前端构建是否成功）
4. **遇到的问题**（如果有）
5. **建议的优化方向**（如果有）

生成完成报告：`docs/handoffs/DATA-WEB-完成报告-Claude.md`

---

## 🚀 开始执行

现在开始执行 DATA-WEB-01/02/03 任务，从 P0-1 开始。

**第一步**：读取 `services/data/src/api/app.py` 文件，了解当前代码结构。

祝执行顺利！🚀

---

**创建时间**：2026-04-13  
**执行人**：Claude Code（新窗口）  
**参考任务**：BACKTEST-WEB-01/02/03、DECISION-WEB-01/02/03（均已 100% 完成）  
**参考报告**：`docs/handoffs/DECISION-WEB-完成报告-Claude.md`
