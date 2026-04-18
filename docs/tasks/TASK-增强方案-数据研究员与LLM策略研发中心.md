# 增强方案 — 数据研究员与 LLM 策略研发中心功能完善

**创建时间**：2026-04-18  
**创建人**：Claude Code  
**状态**：待融入 Atlas 任务体系  
**关联任务**：TASK-0093（data 看板）、TASK-0090（decision 看板）

---

## 一、背景与目标

### 用户需求
Jay.S 明确要求：
1. **重点开发数据研究员和 LLM 自动化策略研发系统**
2. **确保在线模型 Token 消费记录真实体现**
3. **增加功能性和实用性逻辑，不需要管优先级**

### 现状分析

#### 1. LLM 计费追踪器（Decision 服务）
**后端实现状态**：✅ 完整
- 文件：`services/decision/src/billing/billing.py`（1646 行）
- API 端点：`/api/v1/billing/*`（8 个端点）
- 功能：Token 消费追踪、成本计算、用量统计、计费汇总

**前端实现状态**：❌ 缺失
- Dashboard 无 LLM 计费展示页面
- 无法查看实时 Token 消费
- 无法查看成本统计和趋势

#### 2. 数据研究员系统（Data 服务）
**后端实现状态**：⚠️ 部分实现
- 文件：`services/data/src/researcher/`（多个模块）
- API 端点：`/api/v1/researcher/*`（6 个端点）
- 功能：研究员状态、数据源管理、报告列表、触发研究

**报告生成器状态**：⚠️ 功能简陋
- 文件：`services/data/src/researcher/report_generator.py`
- 问题：报告内容单薄、缺乏深度分析、可视化不足

**前端实现状态**：⚠️ 基础实现
- 页面：`services/data/data_web/app/researcher/page.tsx`
- 问题：只有基础控制台，缺乏报告展示和分析功能

#### 3. LLM 策略生成器（Decision 服务）
**脚本实现状态**：✅ 完整
- 文件：`services/decision/scripts/generate_llm_strategies_palm.py`
- 功能：7 种策略矩阵（趋势/均值回归/波动率/动量/套利/事件驱动/多因子）

**集成状态**：❌ 未集成到看板
- 无法从看板触发策略生成
- 无法查看生成历史和结果
- 无法管理生成的策略

---

## 二、增强方案设计

### 方案 A：融入 TASK-0090（Decision 看板）

#### A1. LLM 计费展示页面（新增 P1-8）

**功能点**：
1. **实时 Token 消费监控**
   - 当前会话消费量
   - 今日累计消费
   - 本月累计消费
   - 实时消费速率

2. **成本统计与趋势**
   - 按模型分类统计（GPT-4/Claude/PaLM）
   - 按功能分类统计（策略生成/信号分析/报告生成）
   - 日/周/月趋势图
   - 成本预警阈值设置

3. **用量详情查询**
   - 按时间范围筛选
   - 按模型筛选
   - 按功能模块筛选
   - 导出用量报告

**API 端点**（已存在）：
- `GET /api/v1/billing/usage` - 获取用量统计
- `GET /api/v1/billing/cost` - 获取成本统计
- `GET /api/v1/billing/summary` - 获取计费汇总
- `GET /api/v1/billing/history` - 获取历史记录

**前端文件**（新增）：
- `services/decision/decision_web/app/billing/page.tsx` - 计费页面
- `services/decision/decision_web/components/TokenUsageChart.tsx` - Token 消费图表
- `services/decision/decision_web/components/CostTrendChart.tsx` - 成本趋势图
- `services/decision/decision_web/components/UsageBreakdown.tsx` - 用量分解表

#### A2. LLM 策略研发中心（新增 P1-9）

**功能点**：
1. **策略生成控制台**
   - 选择策略类型（7 种矩阵）
   - 配置生成参数
   - 触发批量生成
   - 查看生成进度

2. **生成历史管理**
   - 生成任务列表
   - 任务状态追踪
   - 生成结果查看
   - 失败任务重试

3. **策略质量评估**
   - 策略参数合理性检查
   - 策略逻辑一致性验证
   - 策略性能预估
   - 策略推荐排序

**API 端点**（需新增）：
- `POST /api/v1/llm/generate` - 触发策略生成
- `GET /api/v1/llm/tasks` - 获取生成任务列表
- `GET /api/v1/llm/tasks/{task_id}` - 获取任务详情
- `POST /api/v1/llm/tasks/{task_id}/retry` - 重试失败任务
- `GET /api/v1/llm/strategies` - 获取生成的策略列表
- `POST /api/v1/llm/strategies/{id}/evaluate` - 评估策略质量

**后端文件**（新增）：
- `services/decision/src/api/routes/llm_generator.py` - LLM 生成器路由
- `services/decision/src/llm/generator_service.py` - 生成器服务封装
- `services/decision/src/llm/strategy_evaluator.py` - 策略评估器

**前端文件**（新增）：
- `services/decision/decision_web/app/llm-lab/page.tsx` - LLM 研发中心页面
- `services/decision/decision_web/components/StrategyGenerator.tsx` - 策略生成器组件
- `services/decision/decision_web/components/GenerationHistory.tsx` - 生成历史组件
- `services/decision/decision_web/components/StrategyEvaluator.tsx` - 策略评估组件

---

### 方案 B：融入 TASK-0093（Data 看板）

#### B1. 研究员报告增强（升级 P1-7）

**当前 P1-7**：数据源详情分析  
**升级为**：研究员报告深度分析

**功能点**：
1. **报告生成增强**
   - 多维度数据分析（价格/成交量/持仓/情绪）
   - 关键事件提取与标注
   - 市场异动检测与解读
   - 趋势预测与风险提示

2. **报告可视化**
   - 交互式图表（K 线/成交量/持仓分布）
   - 关键指标卡片
   - 事件时间轴
   - 情绪热力图

3. **报告管理**
   - 报告列表与筛选
   - 报告详情查看
   - 报告导出（PDF/Markdown）
   - 报告订阅与推送

**后端文件**（修改）：
- `services/data/src/researcher/report_generator.py` - 增强报告生成逻辑
- `services/data/src/researcher/analyzers/` - 新增分析器模块
  - `price_analyzer.py` - 价格分析器
  - `volume_analyzer.py` - 成交量分析器
  - `sentiment_analyzer.py` - 情绪分析器
  - `event_detector.py` - 事件检测器

**前端文件**（新增/修改）：
- `services/data/data_web/app/researcher/reports/page.tsx` - 报告列表页
- `services/data/data_web/app/researcher/reports/[id]/page.tsx` - 报告详情页
- `services/data/data_web/components/ResearchReport.tsx` - 报告展示组件
- `services/data/data_web/components/ReportChart.tsx` - 报告图表组件
- `services/data/data_web/components/EventTimeline.tsx` - 事件时间轴组件

#### B2. 研究员 Token 消费追踪（新增 P1-8）

**功能点**：
1. **研究员专属计费**
   - 按研究任务统计 Token 消费
   - 按数据源统计消费
   - 按报告类型统计消费

2. **成本优化建议**
   - 识别高消费数据源
   - 建议缓存策略
   - 建议采样频率调整

**API 端点**（需新增）：
- `GET /api/v1/researcher/billing` - 获取研究员计费统计
- `GET /api/v1/researcher/billing/by-task` - 按任务统计
- `GET /api/v1/researcher/billing/by-source` - 按数据源统计

**后端文件**（新增）：
- `services/data/src/researcher/billing_tracker.py` - 研究员计费追踪器

**前端文件**（新增）：
- `services/data/data_web/app/researcher/billing/page.tsx` - 研究员计费页面
- `services/data/data_web/components/ResearcherTokenUsage.tsx` - Token 消费组件

---

## 三、实施建议

### 优先级排序

#### 第一优先级（立即实施）
1. **A1. LLM 计费展示页面** - 用户明确要求 Token 消费记录真实体现
2. **B1. 研究员报告增强** - 用户明确要求重点开发数据研究员

#### 第二优先级（紧随其后）
3. **A2. LLM 策略研发中心** - 用户明确要求 LLM 自动化策略研发系统
4. **B2. 研究员 Token 消费追踪** - 与 A1 配套，完整的计费体系

### 融入 Atlas 任务体系的方式

#### 方式 1：作为 P1 扩展（推荐）
- 在 TASK-0090 中新增 P1-8（LLM 计费）、P1-9（LLM 研发中心）
- 在 TASK-0093 中升级 P1-7（报告增强）、新增 P1-8（研究员计费）
- 优点：与现有任务无缝衔接，不打乱 Atlas 计划
- 缺点：需要 Atlas 修订任务文件和白名单

#### 方式 2：作为独立 P2 任务
- 创建 TASK-0090-P2-LLM-增强
- 创建 TASK-0093-P2-研究员增强
- 优点：独立管理，不影响 P0+P1 进度
- 缺点：需要等待 P0+P1 完成后才能开始

#### 方式 3：作为补充任务（最灵活）
- 创建 TASK-0100-LLM-计费与策略研发中心
- 创建 TASK-0101-数据研究员报告增强
- 优点：完全独立，可以并行开发
- 缺点：需要 Atlas 签发新的 Token

### 建议采用方式 1（P1 扩展）

**理由**：
1. 用户明确要求"重点开发"，优先级应该是 P1 而非 P2
2. 这些功能与现有 P1 功能高度相关（都是看板增强）
3. 可以在 Atlas 完成 TASK-0090/0093 的 P0 部分后立即开始
4. 避免创建过多独立任务，保持任务体系简洁

---

## 四、文件白名单预估

### TASK-0090 扩展（+15 文件）

**后端（6 文件）**：
- `services/decision/src/api/routes/llm_generator.py`
- `services/decision/src/llm/generator_service.py`
- `services/decision/src/llm/strategy_evaluator.py`
- `services/decision/tests/test_llm_generator.py`
- `services/decision/tests/test_strategy_evaluator.py`
- `services/decision/pytest.ini`（已存在，修改）

**前端（9 文件）**：
- `services/decision/decision_web/app/billing/page.tsx`
- `services/decision/decision_web/app/llm-lab/page.tsx`
- `services/decision/decision_web/components/TokenUsageChart.tsx`
- `services/decision/decision_web/components/CostTrendChart.tsx`
- `services/decision/decision_web/components/UsageBreakdown.tsx`
- `services/decision/decision_web/components/StrategyGenerator.tsx`
- `services/decision/decision_web/components/GenerationHistory.tsx`
- `services/decision/decision_web/components/StrategyEvaluator.tsx`
- `services/decision/decision_web/lib/decision-api.ts`（已存在，修改）

### TASK-0093 扩展（+12 文件）

**后端（7 文件）**：
- `services/data/src/researcher/report_generator.py`（已存在，修改）
- `services/data/src/researcher/analyzers/__init__.py`
- `services/data/src/researcher/analyzers/price_analyzer.py`
- `services/data/src/researcher/analyzers/volume_analyzer.py`
- `services/data/src/researcher/analyzers/sentiment_analyzer.py`
- `services/data/src/researcher/analyzers/event_detector.py`
- `services/data/src/researcher/billing_tracker.py`

**前端（5 文件）**：
- `services/data/data_web/app/researcher/reports/page.tsx`
- `services/data/data_web/app/researcher/reports/[id]/page.tsx`
- `services/data/data_web/app/researcher/billing/page.tsx`
- `services/data/data_web/components/ResearchReport.tsx`
- `services/data/data_web/components/ResearcherTokenUsage.tsx`

**总计**：27 个文件（13 后端 + 14 前端）

---

## 五、验收标准

### A1. LLM 计费展示页面
- [ ] 可查看实时 Token 消费（当前/今日/本月）
- [ ] 可查看成本统计与趋势图
- [ ] 可按模型/功能筛选用量详情
- [ ] 可导出用量报告

### A2. LLM 策略研发中心
- [ ] 可选择策略类型并触发生成
- [ ] 可查看生成任务列表和状态
- [ ] 可查看生成结果和策略详情
- [ ] 可评估策略质量并查看推荐排序

### B1. 研究员报告增强
- [ ] 报告包含多维度数据分析
- [ ] 报告包含交互式图表
- [ ] 报告包含关键事件时间轴
- [ ] 可查看报告列表并筛选
- [ ] 可导出报告为 PDF/Markdown

### B2. 研究员 Token 消费追踪
- [ ] 可查看研究员专属计费统计
- [ ] 可按任务/数据源统计消费
- [ ] 可查看成本优化建议

---

## 六、下一步行动

### 等待 Jay.S 确认
1. 是否采用方式 1（P1 扩展）融入 Atlas 任务体系？
2. 是否同意上述功能范围和优先级排序？
3. 是否需要调整或补充功能点？

### 等待 Atlas 操作
1. 修订 TASK-0090 和 TASK-0093 任务文件
2. 扩展文件白名单（+27 文件）
3. 签发补充 Token（如需要）

### Claude 准备工作
1. 详细设计 API 接口规范
2. 设计前端组件结构
3. 准备测试用例清单
