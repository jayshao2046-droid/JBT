# TASK-0088 — Backtest 看板全面增强 第二阶段（P2）

**任务编号**：TASK-0088  
**参考**：BACKTEST-WEB-02（Claude 申请）  
**创建时间**：2026-04-13  
**创建人**：Atlas  
**执行人**：Claude Code  
**状态**：🔓 待执行  
**前置**：TASK-0087 完成验收后方可执行

---

## 一、功能范围（P2，6项）

| 编号 | 功能 | 说明 |
|------|------|------|
| P2-1 | 回测结果分析增强 | 月度收益热力图/年度对比/分品种绩效 |
| P2-2 | 策略参数优化器 | 网格搜索/遗传算法/贝叶斯优化 |
| P2-3 | 回测配置可视化编辑 | 时间范围/初始资金/手续费/滑点配置 |
| P2-4 | 回测任务队列管理 | 待执行/执行中/已完成/优先级/取消重试 |
| P2-5 | 回测模板功能 | 预设模板/自定义/导入导出 |
| P2-6 | 多时间框架分析 | 多周期回测/时间框架对比 |

---

## 二、文件白名单（12个文件）

### 后端（Python）

| 操作 | 文件路径 |
|------|---------|
| 修改 | `services/backtest/src/api/app.py` |
| 新建 | `services/backtest/src/stats/optimizer.py` |
| 新建目录 | `services/backtest/src/queue/` |
| 新建 | `services/backtest/src/queue/__init__.py` |
| 新建 | `services/backtest/src/queue/manager.py` |
| 新建 | `services/backtest/tests/test_optimizer.py` |
| 新建 | `services/backtest/tests/test_queue.py` |

### 前端（TypeScript/React）

| 操作 | 文件路径 |
|------|---------|
| 新建目录+页面 | `services/backtest/backtest_web/app/optimizer/page.tsx` |
| 新建 | `services/backtest/backtest_web/components/BacktestAnalysis.tsx` |
| 新建 | `services/backtest/backtest_web/components/ParameterOptimizer.tsx` |
| 新建 | `services/backtest/backtest_web/components/BacktestConfigEditor.tsx` |
| 新建 | `services/backtest/backtest_web/components/BacktestQueue.tsx` |
| 新建 | `services/backtest/backtest_web/components/BacktestTemplates.tsx` |
| 修改 | `services/backtest/backtest_web/lib/backtest-api.ts` |

**总计：14 文件（7 后端 + 7 前端）**

---

## 三、边界约束

1. 严格限于 `services/backtest/**`，禁止跨服务
2. `src/queue/` 为内部任务队列模块，禁止被其他服务 import
3. 优化算法（遗传/贝叶斯）使用现有依赖，不引入新包
4. 不修改 `docker-compose.dev.yml`、`.env.example`、`shared/**`

---

## 四、验收标准

- [ ] `pytest tests/` 全部通过（含 test_optimizer / test_queue）
- [ ] `pnpm build` Compiled successfully
- [ ] P2-1：月度收益热力图显示正常
- [ ] P2-2：参数优化器支持网格搜索
- [ ] P2-3：回测配置编辑器可修改并保存
- [ ] P2-4：任务队列可查看和管理
- [ ] P2-5：模板可保存/加载/导入导出
- [ ] P2-6：多时间框架分析正常

---

## 五、关联文档

- 父任务：[TASK-0087](./TASK-0087-backtest-看板增强-P0P1阶段.md)
- 预审：[TASK-0088-review.md](../reviews/TASK-0088-review.md)
- Token 申请：[BACKTEST-WEB-Token申请-Claude.md](../handoffs/BACKTEST-WEB-Token申请-Claude.md)
