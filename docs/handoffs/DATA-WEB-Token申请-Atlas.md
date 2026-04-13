# 数据端看板全面增强 — Token 申请提示词（给 Atlas）

---

## 📋 任务背景

参考 **backtest 看板**和 **decision 看板**的成功经验（均已 100% 完成，19 项功能），现需要对 **data 服务**的看板进行同等规模的全面增强。

**已完成看板**：
- ✅ backtest 看板：19项功能，25个文件，~3630行代码，13个测试用例
- ✅ decision 看板：19项功能，35个文件，~3600行代码，32个测试用例

现需要将相同的增强方案应用到 **data 服务**。

---

## 🎯 任务目标

对 `services/data/data_web/` 进行全面增强，实现与 backtest/decision 看板同等水平的功能覆盖。

**分三个阶段实施**：
1. **第一阶段（P0+P1）**：核心功能 + 高优先级功能（10项）
2. **第二阶段（P2）**：中优先级功能（6项）
3. **第三阶段（P3）**：高级功能（3项）

---

## 📦 第一阶段（P0+P1）功能清单

### P0 - 核心功能（3项）

#### P0-1：数据采集历史记录
- 后端：新增 `GET /api/v1/data/collection/history` 端点
- 后端：支持 `start_date`、`end_date`、`source` 查询参数
- 前端：采集历史列表，支持查看历史采集记录

#### P0-2：数据源配置验证
- 后端：新增 `POST /api/v1/data/source/validate` 端点
- 后端：数据源连接检查、配置验证、权限检查
- 前端：数据源配置实时验证反馈

#### P0-3：采集进度实时推送
- 后端：新增 `GET /api/v1/data/collection/progress/{id}/stream` 端点（SSE）
- 后端：采集进度百分比、当前阶段、预计完成时间
- 前端：进度条 + 实时状态更新

### P1 - 高优先级功能（7项）

#### P1-1：数据质量 KPI（7个指标）
- 数据完整性、及时性、准确性、一致性
- 采集成功率、平均延迟、错误率
- 后端：`GET /api/v1/data/collection/{id}/quality`
- 前端：`DataQualityKPI.tsx` 组件

#### P1-2：数据源健康 KPI（5个指标）
- 数据源可用性、响应时间、错误率
- 数据新鲜度、覆盖率
- 后端：`GET /api/v1/data/source/{id}/health`
- 前端：`DataSourceHealthKPI.tsx` 组件

#### P1-3：批量采集任务
- 支持多个数据源批量采集
- 支持参数组合批量测试
- 后端：`POST /api/v1/data/collection/batch`
- 前端：批量采集配置界面

#### P1-4：数据源对比
- 支持选择多个数据源对比
- 并排显示质量指标、采集统计、覆盖范围
- 前端：`DataSourceComparison.tsx` 组件

#### P1-5：实时采集告警
- 采集完成通知、异常告警
- 浏览器通知 + 音频告警
- 前端：`lib/notification.ts` + `lib/audio.ts`

#### P1-6：采集统计可视化
- 采集时间分布图、数据源分布图
- 支持缩放、拖拽、标记
- 前端：`CollectionStatsChart.tsx` 组件

#### P1-7：数据源详情分析
- 数据源列表（按可用性/响应时间排序）
- 数据源统计（成功率/延迟/覆盖率）
- 前端：`DataSourceAnalysis.tsx` 组件

---

## 📦 第二阶段（P2）功能清单

### P2-1：数据采集分析增强
- 月度采集热力图
- 年度数据量对比
- 分数据源绩效分析

### P2-2：采集参数优化器
- 参数网格搜索
- 自动调优算法
- 最佳实践推荐

### P2-3：数据源配置可视化编辑
- 数据源参数编辑器
- 采集频率配置
- 重试策略配置

### P2-4：采集任务队列管理
- 查看待执行/执行中/已完成任务
- 任务优先级调整
- 任务取消/重试

### P2-5：数据源模板功能
- 预设模板（股票/期货/宏观/新闻）
- 自定义模板保存
- 模板导入导出

### P2-6：多时间框架分析
- 支持多个时间周期采集
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

### P3-3：数据采集热力图
- 参数热力图（参数组合 vs 成功率）
- 时间热力图（月度采集分布）
- 前端：`CollectionHeatmap.tsx` 组件

---

## 📁 文件白名单（预估）

### 后端文件（Python）

```
services/data/
├── src/
│   ├── api/
│   │   ├── app.py                              # 修改：新增路由
│   │   └── routes/
│   │       └── data_web.py                     # 新建：数据看板专用路由
│   ├── data/
│   │   ├── validator.py                        # 新建：数据源配置验证
│   │   └── progress_tracker.py                 # 新建：采集进度追踪
│   ├── stats/
│   │   ├── __init__.py                         # 新建
│   │   ├── quality.py                          # 新建：数据质量计算
│   │   ├── health.py                           # 新建：数据源健康评估
│   │   └── optimizer.py                        # 新建：采集参数优化
│   └── queue/
│       ├── __init__.py                         # 新建
│       └── manager.py                          # 新建：任务队列管理
└── tests/
    ├── test_stats.py                           # 新建
    ├── test_validator.py                       # 新建
    ├── test_optimizer.py                       # 新建
    └── test_queue.py                           # 新建
```

**预计后端文件**：~15个文件（9个新建 + 1个修改 + 5个测试）

### 前端文件（TypeScript/React）

```
services/data/data_web/
├── app/
│   ├── collections/page.tsx                    # 修改：集成新组件
│   ├── history/page.tsx                        # 新建：采集历史页面
│   └── optimizer/page.tsx                      # 新建：参数优化页面
├── components/
│   ├── DataQualityKPI.tsx                      # 新建：数据质量 KPI
│   ├── DataSourceHealthKPI.tsx                 # 新建：数据源健康 KPI
│   ├── DataSourceComparison.tsx                # 新建：数据源对比
│   ├── CollectionStatsChart.tsx                # 新建：采集统计图
│   ├── DataSourceAnalysis.tsx                  # 新建：数据源分析
│   ├── CollectionAnalysis.tsx                  # 新建：采集分析
│   ├── CollectionOptimizer.tsx                 # 新建：采集优化器
│   ├── DataSourceConfigEditor.tsx              # 新建：配置编辑器
│   ├── CollectionQueue.tsx                     # 新建：任务队列
│   ├── DataSourceTemplates.tsx                 # 新建：模板管理
│   ├── CollectionHeatmap.tsx                   # 新建：热力图
│   ├── ThemeToggle.tsx                         # 新建：主题切换
│   ├── KeyboardShortcutsHelp.tsx               # 新建：快捷键帮助
│   ├── ProgressTracker.tsx                     # 新建：进度追踪
│   └── SourceConfigInput.tsx                   # 新建：配置输入
└── lib/
    ├── data-api.ts                             # 新建：API 客户端
    ├── keyboard.ts                             # 新建：快捷键管理
    ├── notification.ts                         # 新建：通知工具
    └── audio.ts                                # 新建：音频工具
```

**预计前端文件**：~20个文件（17个新建 + 3个修改）

---

## 📊 工作量预估

基于 backtest 和 decision 的实际完成情况：

| 阶段 | 功能数 | 组件数 | 代码量 | 工作量 |
|------|--------|--------|--------|--------|
| 第一阶段（P0+P1） | 10项 | 7个 | ~1600行 | 16-20小时 |
| 第二阶段（P2） | 6项 | 6个 | ~1200行 | 10-12小时 |
| 第三阶段（P3） | 3项 | 3个 | ~800行 | 4-6小时 |
| **总计** | **19项** | **16个** | **~3600行** | **30-38小时** |

---

## 🔐 Token 申请

### 第一阶段 Token（P0+P1）

**任务编号**：DATA-WEB-01  
**文件数量**：~25个文件（10个后端 + 15个前端）  
**有效期**：7天（10080分钟）  
**Agent**：Claude Code

**白名单文件**：
```
# 后端（10个）
services/data/src/api/app.py
services/data/src/api/routes/data_web.py
services/data/src/data/validator.py
services/data/src/data/progress_tracker.py
services/data/src/stats/__init__.py
services/data/src/stats/quality.py
services/data/src/stats/health.py
services/data/tests/test_stats.py
services/data/tests/test_validator.py
services/data/tests/test_data_service.py
services/data/pytest.ini

# 前端（15个）
services/data/data_web/app/history/page.tsx
services/data/data_web/app/collections/page.tsx
services/data/data_web/components/DataQualityKPI.tsx
services/data/data_web/components/DataSourceHealthKPI.tsx
services/data/data_web/components/DataSourceComparison.tsx
services/data/data_web/components/CollectionStatsChart.tsx
services/data/data_web/components/DataSourceAnalysis.tsx
services/data/data_web/components/ProgressTracker.tsx
services/data/data_web/components/SourceConfigInput.tsx
services/data/data_web/lib/data-api.ts
services/data/data_web/lib/notification.ts
services/data/data_web/lib/audio.ts
services/data/data_web/lib/keyboard.ts
```

### 第二阶段 Token（P2）

**任务编号**：DATA-WEB-02  
**文件数量**：~13个文件（4个后端 + 9个前端）  
**有效期**：5天（7200分钟）  
**Agent**：Claude Code

**白名单文件**：
```
# 后端（5个）
services/data/src/api/app.py
services/data/src/stats/optimizer.py
services/data/src/queue/__init__.py
services/data/src/queue/manager.py
services/data/tests/test_optimizer.py
services/data/tests/test_queue.py

# 前端（8个）
services/data/data_web/app/optimizer/page.tsx
services/data/data_web/components/CollectionAnalysis.tsx
services/data/data_web/components/CollectionOptimizer.tsx
services/data/data_web/components/DataSourceConfigEditor.tsx
services/data/data_web/components/CollectionQueue.tsx
services/data/data_web/components/DataSourceTemplates.tsx
services/data/data_web/lib/data-api.ts
```

### 第三阶段 Token（P3）

**任务编号**：DATA-WEB-03  
**文件数量**：~5个文件（全部前端）  
**有效期**：3天（4320分钟）  
**Agent**：Claude Code

**白名单文件**：
```
services/data/data_web/components/CollectionHeatmap.tsx
services/data/data_web/components/ThemeToggle.tsx
services/data/data_web/components/KeyboardShortcutsHelp.tsx
services/data/data_web/lib/keyboard.ts
services/data/data_web/app/collections/page.tsx
```

---

## 📋 验收标准

### 第一阶段验收标准
1. ✅ 采集历史列表可以查看和筛选
2. ✅ 数据源配置有实时验证反馈
3. ✅ 采集进度实时显示（进度条 + 百分比）
4. ✅ 数据质量 KPI 显示 7 个指标
5. ✅ 数据源健康 KPI 显示 5 个指标
6. ✅ 支持批量采集（参数网格）
7. ✅ 支持多个数据源对比
8. ✅ 采集完成有浏览器通知和音频告警
9. ✅ 采集统计图表完整
10. ✅ 数据源分析可以查看和排序

### 第二阶段验收标准
1. ✅ 月度采集热力图显示正常
2. ✅ 采集优化器支持网格搜索
3. ✅ 数据源配置编辑器可以修改并保存
4. ✅ 任务队列可以查看和管理
5. ✅ 模板可以保存、加载和导入导出
6. ✅ 多时间框架分析正常工作

### 第三阶段验收标准
1. ✅ 键盘快捷键系统正常工作
2. ✅ 主题切换功能正常
3. ✅ 采集热力图显示正常

### 测试标准
1. ✅ 后端新增端点全部通过单元测试（≥30 个测试用例）
2. ✅ 前端新增组件无 TypeScript 类型错误
3. ✅ 前端构建成功（`pnpm build` 无错误）
4. ✅ 所有 API 端点有完整的错误处理

---

## 🎯 关键差异点（vs backtest/decision）

1. **数据端特有功能**：
   - 数据源健康监控（可用性/响应时间/错误率）
   - 数据质量评估（完整性/及时性/准确性/一致性）
   - 采集参数优化（频率/重试策略/超时配置）
   - 数据源配置验证（连接检查/权限验证）

2. **数据特点**：
   - 数据采集更实时（需要实时推送）
   - 需要更强的数据源管理能力
   - 需要数据质量评估

3. **性能要求**：
   - 采集任务可能耗时较长（需要进度推送）
   - 需要任务队列管理
   - 需要结果缓存机制

---

## 📝 实施建议

1. **分阶段实施**：
   - 先完成第一阶段（P0+P1），验收通过后再进行第二阶段
   - 每个阶段独立 commit，便于回滚

2. **复用 backtest/decision 代码**：
   - 可以复用的组件：ThemeToggle、KeyboardShortcuts、ProgressTracker
   - 可以复用的工具库：keyboard.ts、notification.ts、audio.ts
   - 可以复用的后端逻辑：QueueManager、ParameterOptimizer

3. **测试优先**：
   - 每个新增功能都要有单元测试
   - 关键功能要有集成测试

4. **文档同步**：
   - 每个阶段完成后生成完成报告
   - 更新 API 文档

---

## 🚀 请求 Atlas 执行

请 Atlas 审核以上方案，并签发三个阶段的 Token：

1. **DATA-WEB-01**（第一阶段）：~25个文件，7天有效期
2. **DATA-WEB-02**（第二阶段）：~13个文件，5天有效期
3. **DATA-WEB-03**（第三阶段）：~5个文件，3天有效期

签发完成后，Claude Code 将按照 backtest/decision 的成功经验，高质量完成所有功能开发。

---

## 📊 参考成果

**backtest 看板已完成**：
- ✅ 19 项功能（100%）
- ✅ 25 个文件
- ✅ ~3630 行代码
- ✅ 13 个测试用例

**decision 看板已完成**：
- ✅ 19 项功能（100%）
- ✅ 35 个文件
- ✅ ~3600 行代码
- ✅ 32 个测试用例

**预期 data 看板成果**：
- 🎯 19 项功能（100%）
- 🎯 ~35 个文件
- 🎯 ~3600 行代码
- 🎯 ≥30 个测试用例
- 🎯 与 backtest/decision 持平或超越

---

**提交人**：Claude Code  
**提交时间**：2026-04-13  
**参考任务**：BACKTEST-WEB-01/02/03、DECISION-WEB-01/02/03（均已 100% 完成）
