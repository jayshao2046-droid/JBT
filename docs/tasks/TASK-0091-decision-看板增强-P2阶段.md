# TASK-0091 — Decision 看板全面增强 第二阶段（P2）

**任务编号**：TASK-0091  
**创建时间**：2026-04-13  
**创建人**：Atlas  
**执行人**：Claude Code  
**状态**：🔓 待执行（与 TASK-0090 同批授权）

---

## 一、功能范围（P2，6项）

| 编号 | 功能 |
|------|------|
| P2-1 | 决策结果分析增强（月度热力图/年度对比/分品种） |
| P2-2 | 策略参数优化器（网格/遗传/贝叶斯） |
| P2-3 | 决策配置可视化编辑（因子权重/风控参数） |
| P2-4 | 决策任务队列管理 |
| P2-5 | 决策模板功能（预设/自定义/导入导出） |
| P2-6 | 多时间框架分析 |

---

## 二、文件白名单（13个文件）

### 后端（Python）

| 操作 | 文件路径 |
|------|---------|
| 修改 | `services/decision/src/api/app.py` |
| 新建 | `services/decision/src/stats/optimizer.py` |
| 新建目录 | `services/decision/src/queue/` |
| 新建 | `services/decision/src/queue/__init__.py` |
| 新建 | `services/decision/src/queue/manager.py` |
| 新建 | `services/decision/tests/test_optimizer.py` |
| 新建 | `services/decision/tests/test_queue.py` |

### 前端（TypeScript/React）

| 操作 | 文件路径 |
|------|---------|
| 新建目录+页面 | `services/decision/decision_web/app/optimizer/page.tsx` |
| 新建 | `services/decision/decision_web/components/DecisionAnalysis.tsx` |
| 新建 | `services/decision/decision_web/components/ParameterOptimizer.tsx` |
| 新建 | `services/decision/decision_web/components/DecisionConfigEditor.tsx` |
| 新建 | `services/decision/decision_web/components/DecisionQueue.tsx` |
| 新建 | `services/decision/decision_web/components/DecisionTemplates.tsx` |
| 修改 | `services/decision/decision_web/lib/decision-api.ts` |

**总计：14 文件（7 后端 + 7 前端）**

---

## 三、边界约束

1. 严格限于 `services/decision/**`
2. 优化算法使用现有依赖，不引入新包
3. queue/ 为内部任务队列，不跨服务
