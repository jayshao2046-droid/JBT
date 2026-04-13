# 决策端看板全面增强 — Token 申请提示词（给 Atlas）

---

## 📋 任务背景

参考 **backtest 看板**的成功经验（BACKTEST-WEB-01/02/03 已 100% 完成，19 项功能），现需要对 **decision 服务**的看板进行同等规模的全面增强。

**backtest 看板已完成**：
- ✅ 第一阶段（P0+P1）：10项功能，~1630行代码
- ✅ 第二阶段（P2）：6项功能，~1200行代码  
- ✅ 第三阶段（P3）：3项功能，~800行代码
- ✅ 总计：19项功能，25个文件，~3630行代码，13个测试用例

现需要将相同的增强方案应用到 **decision 服务**。

---

## 🎯 任务目标

对 `services/decision/decision_web/` 进行全面增强，实现与 backtest 看板同等水平的功能覆盖。

**分三个阶段实施**：
1. **第一阶段（P0+P1）**：核心功能 + 高优先级功能（10项）
2. **第二阶段（P2）**：中优先级功能（6项）
3. **第三阶段（P3）**：高级功能（3项）

---

## 📦 第一阶段（P0+P1）功能清单

### P0 - 核心功能（3项）

#### P0-1：决策历史持久化
- 后端：新增 `GET /api/v1/decision/history` 端点
- 后端：支持 `start_date` 和 `end_date` 查询参数
- 前端：决策历史列表，支持查看历史决策记录

#### P0-2：策略参数实时验证
- 后端：新增 `POST /api/v1/strategy/validate` 端点
- 后端：参数范围检查、类型检查、依赖检查
- 前端：参数输入实时验证反馈

#### P0-3：决策进度实时推送
- 后端：新增 `GET /api/v1/decision/progress` 端点（SSE）
- 后端：决策进度百分比、当前阶段、预计完成时间
- 前端：进度条 + 实时状态更新

### P1 - 高优先级功能（7项）

#### P1-1：决策绩效 KPI（7个指标）
- 信号准确率、平均收益率、最大回撤、夏普比率
- 信号数量、执行成功率、平均响应时间
- 后端：`GET /api/v1/decision/{id}/performance`
- 前端：`PerformanceKPI.tsx` 组件

#### P1-2：决策质量 KPI（5个指标）
- 信号质量评分、因子有效性、策略稳定性
- 风险控制有效性、数据完整性
- 后端：`GET /api/v1/decision/{id}/quality`
- 前端：`DecisionQualityKPI.tsx` 组件

#### P1-3：批量决策功能
- 支持多个策略批量执行
- 支持参数组合批量测试
- 后端：`POST /api/v1/decision/batch`
- 前端：批量决策配置界面

#### P1-4：决策结果对比
- 支持选择多个决策结果对比
- 并排显示绩效指标、信号分布、收益曲线
- 前端：`DecisionComparison.tsx` 组件

#### P1-5：实时决策告警
- 决策完成通知、异常告警
- 浏览器通知 + 音频告警
- 前端：`lib/notification.ts` + `lib/audio.ts`

#### P1-6：信号分布可视化
- 信号时间分布图、信号类型分布图
- 支持缩放、拖拽、标记
- 前端：`SignalDistributionChart.tsx` 组件

#### P1-7：因子分析详情
- 因子列表（按贡献度/相关性排序）
- 因子统计（有效性/稳定性/覆盖率）
- 前端：`FactorAnalysis.tsx` 组件

---

## 📦 第二阶段（P2）功能清单

### P2-1：决策结果分析增强
- 月度信号热力图
- 年度收益对比
- 分品种绩效分析

### P2-2：策略参数优化器
- 参数网格搜索
- 遗传算法优化
- 贝叶斯优化
- 后端：`POST /api/v1/optimize/grid`
- 前端：`ParameterOptimizer.tsx` 组件

### P2-3：决策配置可视化编辑
- 策略参数编辑器
- 因子权重配置
- 风控参数配置

### P2-4：决策任务队列管理
- 查看待执行/执行中/已完成任务
- 任务优先级调整
- 任务取消/重试
- 后端：`GET /api/v1/decision/queue`
- 前端：`DecisionQueue.tsx` 组件

### P2-5：决策模板功能
- 预设模板（趋势/反转/套利）
- 自定义模板保存
- 模板导入导出

### P2-6：多时间框架分析
- 支持多个时间周期决策
- 时间框架对比

---

## 📦 第三阶段（P3）功能清单

### P3-1：键盘快捷键系统
- 8个全局快捷键
- 快捷键帮助面板
- 前端：`lib/keyboard.ts` + `KeyboardShortcutsHelp.tsx`

### P3-2：主题切换
- 暗色/亮色模式
- 主题持久化
- 前端：`ThemeToggle.tsx` 组件

### P3-3：决策热力图
- 参数热力图（参数组合 vs 收益率）
- 时间热力图（月度信号分布）
- 前端：`DecisionHeatmap.tsx` 组件

---

## 📁 文件白名单（预估）

### 后端文件（Python）

```
services/decision/
├── src/
│   ├── api/
│   │   └── app.py                          # 修改：新增 15+ 个端点
│   ├── decision/
│   │   ├── validator.py                    # 新建：参数验证
│   │   └── progress_tracker.py             # 新建：进度追踪
│   ├── stats/
│   │   ├── __init__.py                     # 新建
│   │   ├── performance.py                  # 新建：绩效统计
│   │   ├── quality.py                      # 新建：质量评估
│   │   └── optimizer.py                    # 新建：参数优化
│   └── queue/
│       ├── __init__.py                     # 新建
│       └── manager.py                      # 新建：任务队列管理
└── tests/
    ├── test_stats.py                       # 新建
    ├── test_validator.py                   # 新建
    ├── test_optimizer.py                   # 新建
    └── test_queue.py                       # 新建
```

**预计后端文件**：~15个文件（8个新建 + 7个修改）

### 前端文件（TypeScript/React）

```
services/decision/decision_web/
├── app/
│   ├── decisions/page.tsx                  # 修改：集成新组件
│   ├── history/page.tsx                    # 新建：决策历史页面
│   └── optimizer/page.tsx                  # 新建：参数优化页面
├── components/
│   ├── PerformanceKPI.tsx                  # 新建：绩效 KPI
│   ├── DecisionQualityKPI.tsx              # 新建：质量 KPI
│   ├── DecisionComparison.tsx              # 新建：结果对比
│   ├── SignalDistributionChart.tsx         # 新建：信号分布图
│   ├── FactorAnalysis.tsx                  # 新建：因子分析
│   ├── DecisionAnalysis.tsx                # 新建：结果分析
│   ├── ParameterOptimizer.tsx              # 新建：参数优化器
│   ├── DecisionConfigEditor.tsx            # 新建：配置编辑器
│   ├── DecisionQueue.tsx                   # 新建：任务队列
│   ├── DecisionTemplates.tsx               # 新建：模板管理
│   ├── DecisionHeatmap.tsx                 # 新建：热力图
│   ├── ThemeToggle.tsx                     # 新建：主题切换
│   ├── KeyboardShortcutsHelp.tsx           # 新建：快捷键帮助
│   ├── ProgressTracker.tsx                 # 新建：进度追踪
│   └── ParamInput.tsx                      # 新建：参数输入
└── lib/
    ├── decision-api.ts                     # 新建：API 客户端
    ├── keyboard.ts                         # 新建：快捷键管理
    ├── notification.ts                     # 新建：通知工具
    └── audio.ts                            # 新建：音频工具
```

**预计前端文件**：~20个文件（17个新建 + 3个修改）

---

## 📊 工作量预估

基于 backtest 的实际完成情况：

| 阶段 | 功能数 | 组件数 | 代码量 | 工作量 |
|------|--------|--------|--------|--------|
| 第一阶段（P0+P1） | 10项 | 7个 | ~1630行 | 16-20小时 |
| 第二阶段（P2） | 6项 | 6个 | ~1200行 | 10-12小时 |
| 第三阶段（P3） | 3项 | 3个 | ~800行 | 4-6小时 |
| **总计** | **19项** | **16个** | **~3630行** | **30-38小时** |

---

## 🔐 Token 申请

### 第一阶段 Token（P0+P1）

**任务编号**：DECISION-WEB-01  
**文件数量**：~25个文件（10个后端 + 15个前端）  
**有效期**：7天（10080分钟）  
**Agent**：Claude Code

**白名单文件**：
```
# 后端（10个）
services/decision/src/api/app.py
services/decision/src/decision/validator.py
services/decision/src/decision/progress_tracker.py
services/decision/src/stats/__init__.py
services/decision/src/stats/performance.py
services/decision/src/stats/quality.py
services/decision/tests/test_stats.py
services/decision/tests/test_validator.py
services/decision/tests/test_decision_service.py
services/decision/pytest.ini

# 前端（15个）
services/decision/decision_web/app/history/page.tsx
services/decision/decision_web/app/decisions/page.tsx
services/decision/decision_web/components/PerformanceKPI.tsx
services/decision/decision_web/components/DecisionQualityKPI.tsx
services/decision/decision_web/components/DecisionComparison.tsx
services/decision/decision_web/components/SignalDistributionChart.tsx
services/decision/decision_web/components/FactorAnalysis.tsx
services/decision/decision_web/components/ProgressTracker.tsx
services/decision/decision_web/components/ParamInput.tsx
services/decision/decision_web/lib/decision-api.ts
services/decision/decision_web/lib/notification.ts
services/decision/decision_web/lib/audio.ts
services/decision/decision_web/lib/keyboard.ts
```

### 第二阶段 Token（P2）

**任务编号**：DECISION-WEB-02  
**文件数量**：~12个文件（4个后端 + 8个前端）  
**有效期**：5天（7200分钟）  
**Agent**：Claude Code

**白名单文件**：
```
# 后端（4个）
services/decision/src/api/app.py
services/decision/src/stats/optimizer.py
services/decision/src/queue/__init__.py
services/decision/src/queue/manager.py

# 前端（8个）
services/decision/decision_web/app/optimizer/page.tsx
services/decision/decision_web/components/DecisionAnalysis.tsx
services/decision/decision_web/components/ParameterOptimizer.tsx
services/decision/decision_web/components/DecisionConfigEditor.tsx
services/decision/decision_web/components/DecisionQueue.tsx
services/decision/decision_web/components/DecisionTemplates.tsx
services/decision/decision_web/lib/decision-api.ts
```

### 第三阶段 Token（P3）

**任务编号**：DECISION-WEB-03  
**文件数量**：~5个文件（全部前端）  
**有效期**：3天（4320分钟）  
**Agent**：Claude Code

**白名单文件**：
```
services/decision/decision_web/components/DecisionHeatmap.tsx
services/decision/decision_web/components/ThemeToggle.tsx
services/decision/decision_web/components/KeyboardShortcutsHelp.tsx
services/decision/decision_web/lib/keyboard.ts
```

---

## 📋 验收标准

### 第一阶段验收标准
1. ✅ 决策历史列表可以查看和筛选
2. ✅ 策略参数输入有实时验证反馈
3. ✅ 决策进度实时显示（进度条 + 百分比）
4. ✅ 绩效 KPI 显示 7 个指标
5. ✅ 质量 KPI 显示 5 个指标
6. ✅ 支持批量决策（参数网格）
7. ✅ 支持多个决策结果对比
8. ✅ 决策完成有浏览器通知和音频告警
9. ✅ 信号分布图表完整
10. ✅ 因子分析可以查看和排序

### 第二阶段验收标准
1. ✅ 月度信号热力图显示正常
2. ✅ 参数优化器支持网格搜索
3. ✅ 决策配置编辑器可以修改并保存
4. ✅ 任务队列可以查看和管理
5. ✅ 模板可以保存、加载和导入导出
6. ✅ 多时间框架分析正常工作

### 第三阶段验收标准
1. ✅ 键盘快捷键系统正常工作
2. ✅ 主题切换功能正常
3. ✅ 决策热力图显示正常

### 测试标准
1. ✅ 后端新增端点全部通过单元测试（≥30 个测试用例）
2. ✅ 前端新增组件无 TypeScript 类型错误
3. ✅ 前端构建成功（`pnpm build` 无错误）
4. ✅ 所有 API 端点有完整的错误处理

---

## 🎯 关键差异点（vs backtest）

1. **决策特有功能**：
   - 信号分布可视化（时间分布/类型分布）
   - 因子分析详情（贡献度/相关性/有效性）
   - 策略参数优化器（网格搜索/遗传算法）
   - 决策质量评估（信号质量/因子有效性/策略稳定性）

2. **数据特点**：
   - 决策数据更实时（需要实时推送）
   - 需要更强的因子分析能力
   - 需要信号质量评估

3. **性能要求**：
   - 决策任务可能耗时较长（需要进度推送）
   - 需要任务队列管理
   - 需要结果缓存机制

---

## 📝 实施建议

1. **分阶段实施**：
   - 先完成第一阶段（P0+P1），验收通过后再进行第二阶段
   - 每个阶段独立 commit，便于回滚

2. **复用 backtest 代码**：
   - 可以复用的组件：PerformanceKPI、ThemeToggle、KeyboardShortcuts
   - 可以复用的工具库：keyboard.ts、notification.ts、audio.ts
   - 可以复用的后端逻辑：PerformanceCalculator、QualityCalculator

3. **测试优先**：
   - 每个新增功能都要有单元测试
   - 关键功能要有集成测试

4. **文档同步**：
   - 每个阶段完成后生成完成报告
   - 更新 API 文档

---

## 🚀 请求 Atlas 执行

请 Atlas 审核以上方案，并签发三个阶段的 Token：

1. **DECISION-WEB-01**（第一阶段）：~25个文件，7天有效期
2. **DECISION-WEB-02**（第二阶段）：~12个文件，5天有效期
3. **DECISION-WEB-03**（第三阶段）：~5个文件，3天有效期

签发完成后，Claude Code 将按照 backtest 的成功经验，高质量完成所有功能开发。

---

## 📊 参考成果

**backtest 看板已完成**：
- ✅ 19 项功能（100%）
- ✅ 25 个文件
- ✅ ~3630 行代码
- ✅ 13 个测试用例
- ✅ 11 个 Commit（含报告）
- ✅ 代码质量：优秀
- ✅ 测试覆盖：良好
- ✅ 文档完整性：完整

**预期 decision 看板成果**：
- 🎯 19 项功能（100%）
- 🎯 25 个文件
- 🎯 ~3630 行代码
- 🎯 ≥30 个测试用例
- 🎯 代码质量：优秀
- 🎯 与 backtest 持平或超越

---

**提交人**：Claude Code  
**提交时间**：2026-04-13  
**参考任务**：BACKTEST-WEB-01/02/03（已 100% 完成）  
**完成报告**：`docs/handoffs/BACKTEST-WEB-最终完成报告-Claude.md`
