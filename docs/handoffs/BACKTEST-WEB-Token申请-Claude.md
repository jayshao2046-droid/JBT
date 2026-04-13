# 回测端看板全面增强 — Token 申请提示词

---

## 📋 任务背景

参考 sim-trading 看板的成功经验（SIMWEB-01/02/03 已完成 19 项功能），现需要对 backtest 服务的看板进行同等规模的全面增强。

sim-trading 看板已完成：
- ✅ 第一阶段（P0+P1）：10项功能，5个组件，~1800行代码
- ✅ 第二阶段（P2）：6项功能，6个组件，~1100行代码  
- ✅ 第三阶段（P3）：3项功能，3个组件，~265行代码
- ✅ 总计：19项功能，14个组件，~3165行代码，100%完成

现需要将相同的增强方案应用到 backtest 服务。

---

## 🎯 任务目标

对 `services/backtest/backtest_web/` 进行全面增强，实现与 sim-trading 看板同等水平的功能覆盖。

**分三个阶段实施**：
1. **第一阶段（P0+P1）**：核心功能 + 高优先级功能（10项）
2. **第二阶段（P2）**：中优先级功能（6项）
3. **第三阶段（P3）**：高级功能（3项）

---

## 📦 第一阶段（P0+P1）功能清单

### P0 - 核心功能（3项）

#### P0-1：回测结果历史持久化
- 后端：新增 `GET /api/v1/backtest/history` 端点
- 后端：`BacktestService` 新增历史记录存储
- 前端：回测结果列表，支持查看历史回测

#### P0-2：策略参数实时验证
- 后端：新增 `POST /api/v1/strategy/validate` 端点
- 后端：参数范围检查、类型检查、依赖检查
- 前端：参数输入实时验证反馈

#### P0-3：回测进度实时推送
- 后端：新增 `GET /api/v1/backtest/progress` 端点（SSE）
- 后端：回测进度百分比、当前日期、预计完成时间
- 前端：进度条 + 实时状态更新

### P1 - 高优先级功能（7项）

#### P1-1：回测绩效 KPI（7个指标）
- 年化收益率、最大回撤、夏普比率、卡玛比率
- 胜率、盈亏比、总交易次数
- 后端：`GET /api/v1/backtest/{id}/performance`
- 前端：`PerformanceKPI.tsx` 组件

#### P1-2：回测质量 KPI（5个指标）
- 样本外表现、过拟合检测、稳定性评分
- 参数敏感度、数据质量评分
- 后端：`GET /api/v1/backtest/{id}/quality`
- 前端：`BacktestQualityKPI.tsx` 组件

#### P1-3：批量回测功能
- 支持多个参数组合批量回测
- 支持参数网格搜索
- 后端：`POST /api/v1/backtest/batch`
- 前端：批量回测配置界面

#### P1-4：回测结果对比
- 支持选择多个回测结果对比
- 并排显示绩效指标、权益曲线、回撤曲线
- 前端：`BacktestComparison.tsx` 组件

#### P1-5：实时回测告警
- 回测完成通知、异常告警
- 浏览器通知 + 音频告警
- 前端：`lib/notification.ts` + `lib/audio.ts`

#### P1-6：权益曲线技术分析
- 权益曲线 + 回撤曲线 + 水下曲线
- 支持缩放、拖拽、标记
- 前端：`EquityCurveChart.tsx` 组件

#### P1-7：交易明细分析
- 交易列表（按盈亏/时间/品种排序）
- 交易统计（胜率/盈亏比/平均持仓时间）
- 前端：`TradeDetailAnalysis.tsx` 组件

---

## 📦 第二阶段（P2）功能清单

### P2-1：回测结果分析增强
- 月度收益热力图
- 年度收益对比
- 分品种绩效分析
- 前端：`BacktestAnalysis.tsx` 组件

### P2-2：策略参数优化器
- 参数网格搜索
- 遗传算法优化
- 贝叶斯优化
- 后端：`POST /api/v1/optimize/grid`
- 前端：`ParameterOptimizer.tsx` 组件

### P2-3：回测配置可视化编辑
- 回测时间范围选择器
- 初始资金配置
- 手续费/滑点配置
- 前端：`BacktestConfigEditor.tsx` 组件

### P2-4：回测任务队列管理
- 查看待执行/执行中/已完成任务
- 任务优先级调整
- 任务取消/重试
- 后端：`GET /api/v1/backtest/queue`
- 前端：`BacktestQueue.tsx` 组件

### P2-5：回测模板功能
- 预设模板（日内/趋势/套利）
- 自定义模板保存
- 模板导入导出
- 前端：`BacktestTemplates.tsx` 组件

### P2-6：多时间框架分析
- 支持多个时间周期回测
- 时间框架对比
- 前端：多周期切换按钮

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

### P3-3：回测热力图
- 参数热力图（参数组合 vs 收益率）
- 时间热力图（月度收益分布）
- 前端：`BacktestHeatmap.tsx` 组件

---

## 📁 文件白名单（预估）

### 后端文件（Python）

```
services/backtest/
├── src/
│   ├── api/
│   │   └── app.py                          # 修改：新增 15+ 个端点
│   ├── backtest/
│   │   ├── service.py                      # 修改：历史记录、进度推送
│   │   └── validator.py                    # 新建：参数验证
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
services/backtest/backtest_web/
├── app/
│   ├── backtest/page.tsx                   # 修改：集成新组件
│   ├── results/page.tsx                    # 修改：回测结果页
│   └── optimizer/page.tsx                  # 修改：参数优化页
├── components/
│   ├── PerformanceKPI.tsx                  # 新建：绩效 KPI
│   ├── BacktestQualityKPI.tsx              # 新建：质量 KPI
│   ├── BacktestComparison.tsx              # 新建：结果对比
│   ├── EquityCurveChart.tsx                # 新建：权益曲线
│   ├── TradeDetailAnalysis.tsx             # 新建：交易明细
│   ├── BacktestAnalysis.tsx                # 新建：结果分析
│   ├── ParameterOptimizer.tsx              # 新建：参数优化器
│   ├── BacktestConfigEditor.tsx            # 新建：配置编辑器
│   ├── BacktestQueue.tsx                   # 新建：任务队列
│   ├── BacktestTemplates.tsx               # 新建：模板管理
│   ├── BacktestHeatmap.tsx                 # 新建：热力图
│   ├── ThemeToggle.tsx                     # 新建：主题切换
│   └── KeyboardShortcutsHelp.tsx           # 新建：快捷键帮助
└── lib/
    ├── backtest-api.ts                     # 修改：新增 API 方法
    ├── keyboard.ts                         # 新建：快捷键管理
    ├── notification.ts                     # 新建：通知工具
    └── audio.ts                            # 新建：音频工具
```

**预计前端文件**：~20个文件（16个新建 + 4个修改）

---

## 📊 工作量预估

基于 sim-trading 的实际完成情况：

| 阶段 | 功能数 | 组件数 | 代码量 | 工作量 |
|------|--------|--------|--------|--------|
| 第一阶段（P0+P1） | 10项 | 7个 | ~2000行 | 16-20小时 |
| 第二阶段（P2） | 6项 | 6个 | ~1200行 | 10-12小时 |
| 第三阶段（P3） | 3项 | 3个 | ~300行 | 4-6小时 |
| **总计** | **19项** | **16个** | **~3500行** | **30-38小时** |

---

## 🔐 Token 申请

### 第一阶段 Token（P0+P1）

**任务编号**：BACKTEST-WEB-01  
**文件数量**：~25个文件（10个后端 + 15个前端）  
**有效期**：7天（10080分钟）  
**Agent**：Claude Code

**白名单文件**：
```
# 后端（10个）
services/backtest/src/api/app.py
services/backtest/src/backtest/service.py
services/backtest/src/backtest/validator.py
services/backtest/src/stats/__init__.py
services/backtest/src/stats/performance.py
services/backtest/src/stats/quality.py
services/backtest/tests/test_stats.py
services/backtest/tests/test_validator.py
services/backtest/tests/test_backtest_service.py
services/backtest/pytest.ini

# 前端（15个）
services/backtest/backtest_web/app/backtest/page.tsx
services/backtest/backtest_web/app/results/page.tsx
services/backtest/backtest_web/components/PerformanceKPI.tsx
services/backtest/backtest_web/components/BacktestQualityKPI.tsx
services/backtest/backtest_web/components/BacktestComparison.tsx
services/backtest/backtest_web/components/EquityCurveChart.tsx
services/backtest/backtest_web/components/TradeDetailAnalysis.tsx
services/backtest/backtest_web/lib/backtest-api.ts
services/backtest/backtest_web/lib/notification.ts
services/backtest/backtest_web/lib/audio.ts
services/backtest/backtest_web/public/alert.mp3
```

### 第二阶段 Token（P2）

**任务编号**：BACKTEST-WEB-02  
**文件数量**：~12个文件（4个后端 + 8个前端）  
**有效期**：5天（7200分钟）  
**Agent**：Claude Code

**白名单文件**：
```
# 后端（4个）
services/backtest/src/api/app.py
services/backtest/src/stats/optimizer.py
services/backtest/src/queue/__init__.py
services/backtest/src/queue/manager.py

# 前端（8个）
services/backtest/backtest_web/app/optimizer/page.tsx
services/backtest/backtest_web/components/BacktestAnalysis.tsx
services/backtest/backtest_web/components/ParameterOptimizer.tsx
services/backtest/backtest_web/components/BacktestConfigEditor.tsx
services/backtest/backtest_web/components/BacktestQueue.tsx
services/backtest/backtest_web/components/BacktestTemplates.tsx
services/backtest/backtest_web/lib/backtest-api.ts
```

### 第三阶段 Token（P3）

**任务编号**：BACKTEST-WEB-03  
**文件数量**：~5个文件（全部前端）  
**有效期**：3天（4320分钟）  
**Agent**：Claude Code

**白名单文件**：
```
services/backtest/backtest_web/components/BacktestHeatmap.tsx
services/backtest/backtest_web/components/ThemeToggle.tsx
services/backtest/backtest_web/components/KeyboardShortcutsHelp.tsx
services/backtest/backtest_web/lib/keyboard.ts
```

---

## 📋 验收标准

### 第一阶段验收标准
1. ✅ 回测历史列表可以查看和筛选
2. ✅ 策略参数输入有实时验证反馈
3. ✅ 回测进度实时显示（进度条 + 百分比）
4. ✅ 绩效 KPI 显示 7 个指标
5. ✅ 质量 KPI 显示 5 个指标
6. ✅ 支持批量回测（参数网格）
7. ✅ 支持多个回测结果对比
8. ✅ 回测完成有浏览器通知和音频告警
9. ✅ 权益曲线图表完整（权益/回撤/水下）
10. ✅ 交易明细可以查看和排序

### 第二阶段验收标准
1. ✅ 月度收益热力图显示正常
2. ✅ 参数优化器支持网格搜索
3. ✅ 回测配置编辑器可以修改并保存
4. ✅ 任务队列可以查看和管理
5. ✅ 模板可以保存、加载和导入导出
6. ✅ 多时间框架分析正常工作

### 第三阶段验收标准
1. ✅ 键盘快捷键系统正常工作
2. ✅ 主题切换功能正常
3. ✅ 回测热力图显示正常

### 测试标准
1. ✅ 后端新增端点全部通过单元测试（≥30 个测试用例）
2. ✅ 前端新增组件无 TypeScript 类型错误
3. ✅ 前端构建成功（`pnpm build` 无错误）
4. ✅ 所有 API 端点有完整的错误处理

---

## 🎯 关键差异点（vs sim-trading）

1. **回测特有功能**：
   - 参数优化器（网格搜索/遗传算法）
   - 回测质量评估（过拟合检测/稳定性评分）
   - 批量回测（参数组合）
   - 回测结果对比

2. **数据特点**：
   - 回测数据量更大（历史数据）
   - 需要更强的数据可视化能力
   - 需要参数敏感度分析

3. **性能要求**：
   - 回测任务可能耗时较长（需要进度推送）
   - 需要任务队列管理
   - 需要结果缓存机制

---

## 📝 实施建议

1. **分阶段实施**：
   - 先完成第一阶段（P0+P1），验收通过后再进行第二阶段
   - 每个阶段独立 commit，便于回滚

2. **复用 sim-trading 代码**：
   - 可以复用的组件：PerformanceKPI、ThemeToggle、KeyboardShortcuts
   - 可以复用的工具库：keyboard.ts、notification.ts、audio.ts

3. **测试优先**：
   - 每个新增功能都要有单元测试
   - 关键功能要有集成测试

4. **文档同步**：
   - 每个阶段完成后生成完成报告
   - 更新 API 文档

---

## 🚀 请求 Atlas 执行

请 Atlas 审核以上方案，并签发三个阶段的 Token：

1. **BACKTEST-WEB-01**（第一阶段）：~25个文件，7天有效期
2. **BACKTEST-WEB-02**（第二阶段）：~12个文件，5天有效期
3. **BACKTEST-WEB-03**（第三阶段）：~5个文件，3天有效期

签发完成后，Claude Code 将按照 sim-trading 的成功经验，高质量完成所有功能开发。

---

**提交人**：Claude Code  
**提交时间**：2026-04-13  
**参考任务**：SIMWEB-01/02/03（已 100% 完成）
