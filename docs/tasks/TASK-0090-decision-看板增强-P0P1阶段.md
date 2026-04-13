# TASK-0090 — Decision 看板全面增强 第一阶段（P0+P1）

**任务编号**：TASK-0090  
**参考**：DECISION-WEB-01（Claude 申请）  
**创建时间**：2026-04-13  
**创建人**：Atlas  
**执行人**：Claude Code  
**状态**：🔓 待执行

---

## 一、功能范围（P0+P1，10项）

### P0（3项）
| 编号 | 功能 |
|------|------|
| P0-1 | 决策历史持久化：`GET /api/v1/decision/history` |
| P0-2 | 策略参数实时验证：`POST /api/v1/strategy/validate` |
| P0-3 | 决策进度实时推送：SSE `GET /api/v1/decision/progress` |

### P1（7项）
| 编号 | 功能 |
|------|------|
| P1-1 | 决策绩效 KPI（7指标） |
| P1-2 | 决策质量 KPI（5指标） |
| P1-3 | 批量决策功能 |
| P1-4 | 决策结果对比 |
| P1-5 | 实时决策告警（浏览器通知+音频） |
| P1-6 | 信号分布可视化 |
| P1-7 | 因子分析详情 |

---

## 二、文件白名单（23个文件）

### 后端（Python）

| 操作 | 文件路径 |
|------|---------|
| 修改 | `services/decision/src/api/app.py` |
| 新建 | `services/decision/src/decision/validator.py` |
| 新建 | `services/decision/src/decision/progress_tracker.py` |
| 新建目录 | `services/decision/src/stats/` |
| 新建 | `services/decision/src/stats/__init__.py` |
| 新建 | `services/decision/src/stats/performance.py` |
| 新建 | `services/decision/src/stats/quality.py` |
| 新建 | `services/decision/tests/test_stats.py` |
| 新建 | `services/decision/tests/test_validator.py` |
| 新建 | `services/decision/tests/test_decision_service.py` |
| 新建 | `services/decision/pytest.ini` |

### 前端（TypeScript/React）

| 操作 | 文件路径 |
|------|---------|
| 新建目录+页面 | `services/decision/decision_web/app/history/page.tsx` |
| 修改 | `services/decision/decision_web/app/decisions/page.tsx` |
| 新建 | `services/decision/decision_web/components/PerformanceKPI.tsx` |
| 新建 | `services/decision/decision_web/components/DecisionQualityKPI.tsx` |
| 新建 | `services/decision/decision_web/components/DecisionComparison.tsx` |
| 新建 | `services/decision/decision_web/components/SignalDistributionChart.tsx` |
| 新建 | `services/decision/decision_web/components/FactorAnalysis.tsx` |
| 新建 | `services/decision/decision_web/components/ProgressTracker.tsx` |
| 新建 | `services/decision/decision_web/components/ParamInput.tsx` |
| 修改 | `services/decision/decision_web/lib/decision-api.ts` |
| 新建 | `services/decision/decision_web/lib/notification.ts` |
| 新建 | `services/decision/decision_web/lib/audio.ts` |

**总计：23 文件（11 后端 + 12 前端）**

---

## 三、边界约束

1. 严格限于 `services/decision/**`，禁止跨服务
2. `src/stats/` 为内部统计模块，不被其他服务 import
3. 历史数据只保留内存/本地文件，不引入数据库
4. 不引入新的 Python 或 npm 依赖包
5. 不修改 `docker-compose.dev.yml`、`.env.example`、`shared/**`

---

## 四、验收标准

- [ ] `pytest tests/` → ≥30 个测试用例通过
- [ ] `pnpm build` → Compiled successfully
- [ ] P0-1：决策历史可查看/筛选
- [ ] P0-2：参数输入实时验证反馈
- [ ] P0-3：决策进度条实时显示
- [ ] P1-1/P1-2：KPI 指标完整显示
- [ ] P1-3：批量决策可用
- [ ] P1-4：多结果对比可用
- [ ] P1-5：浏览器通知+音频告警
- [ ] P1-6/P1-7：图表和分析页面正常

---

## 五、阶段规划

| 阶段 | 任务编号 | 状态 |
|------|---------|------|
| 第一阶段（P0+P1） | TASK-0090 | 🔓 当前 |
| 第二阶段（P2） | TASK-0091 | 🔓 同批签发 |
| 第三阶段（P3） | TASK-0092 | 🔓 同批签发 |
