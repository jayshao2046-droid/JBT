# TASK-0087 — Backtest 看板全面增强 第一阶段（P0+P1）

**任务编号**：TASK-0087  
**参考**：BACKTEST-WEB-01（Claude 申请）  
**创建时间**：2026-04-13  
**创建人**：Atlas  
**执行人**：Claude Code  
**状态**：🔓 待执行  
**父背景**：sim-trading SIMWEB-01/02/03 已 100% 完成，以相同模式增强 backtest 服务

---

## 一、任务背景

对 `services/backtest/` 进行全面增强，实现与 sim-trading 看板同等水平的功能覆盖。  
本任务为第一阶段，涵盖 P0（核心功能）和 P1（高优先级功能）共 10 项。

---

## 二、功能范围

### P0 — 核心功能（3项）

| 编号 | 功能 | 说明 |
|------|------|------|
| P0-1 | 回测结果历史持久化 | 历史记录存储 + `GET /api/v1/backtest/history` |
| P0-2 | 策略参数实时验证 | `POST /api/v1/strategy/validate` + 前端实时反馈 |
| P0-3 | 回测进度实时推送 | SSE `GET /api/v1/backtest/progress` + 前端进度条 |

### P1 — 高优先级功能（7项）

| 编号 | 功能 | 说明 |
|------|------|------|
| P1-1 | 回测绩效 KPI（7指标） | 年化收益/最大回撤/夏普/卡玛/胜率/盈亏比/总交易次数 |
| P1-2 | 回测质量 KPI（5指标） | 样本外表现/过拟合检测/稳定性/参数敏感度/数据质量 |
| P1-3 | 批量回测功能 | 参数网格搜索 + `POST /api/v1/backtest/batch` |
| P1-4 | 回测结果对比 | 多结果并排对比（绩效/权益曲线/回撤） |
| P1-5 | 实时回测告警 | 浏览器通知 + 音频告警 |
| P1-6 | 权益曲线技术分析 | 权益/回撤/水下曲线，支持缩放拖拽 |
| P1-7 | 交易明细分析 | 交易列表排序 + 交易统计 |

---

## 三、文件白名单（21个文件）

### 后端（Python）

| 操作 | 文件路径 |
|------|---------|
| 修改 | `services/backtest/src/api/app.py` |
| 新建 | `services/backtest/src/backtest/service.py` |
| 新建 | `services/backtest/src/backtest/validator.py` |
| 新建目录 | `services/backtest/src/stats/` |
| 新建 | `services/backtest/src/stats/__init__.py` |
| 新建 | `services/backtest/src/stats/performance.py` |
| 新建 | `services/backtest/src/stats/quality.py` |
| 新建 | `services/backtest/tests/test_stats.py` |
| 新建 | `services/backtest/tests/test_validator.py` |
| 新建 | `services/backtest/tests/test_backtest_service.py` |
| 新建 | `services/backtest/pytest.ini` |

### 前端（TypeScript/React）

| 操作 | 文件路径 |
|------|---------|
| 新建目录+页面 | `services/backtest/backtest_web/app/backtest/page.tsx` |
| 新建目录+页面 | `services/backtest/backtest_web/app/results/page.tsx` |
| 新建 | `services/backtest/backtest_web/components/PerformanceKPI.tsx` |
| 新建 | `services/backtest/backtest_web/components/BacktestQualityKPI.tsx` |
| 新建 | `services/backtest/backtest_web/components/BacktestComparison.tsx` |
| 新建 | `services/backtest/backtest_web/components/EquityCurveChart.tsx` |
| 新建 | `services/backtest/backtest_web/components/TradeDetailAnalysis.tsx` |
| 修改 | `services/backtest/backtest_web/lib/backtest-api.ts` |
| 新建 | `services/backtest/backtest_web/lib/notification.ts` |
| 新建 | `services/backtest/backtest_web/lib/audio.ts` |
| 新建 | `services/backtest/backtest_web/public/alert.mp3` |

**总计：21 文件（11 后端 + 10 前端）**  
（申请文档估计 25 个，实际经 Atlas 核对后为 21 个精确文件）

---

## 四、边界约束

1. 严格限于 `services/backtest/**`，禁止触及其他服务
2. 禁止修改 `docker-compose.dev.yml`、`.env.example`、`shared/**`
3. `src/stats/` 为 backtest 内部模块，禁止被其他服务 import
4. 历史数据只保留内存/文件，不引入数据库
5. alert.mp3 使用 Creative Commons 免版权素材或 AudioContext 生成
6. 不引入新的 Python 或 npm 依赖包（使用现有依赖）

---

## 五、验收标准

- [ ] `pytest tests/` → ≥30 个测试用例通过（含新增 test_stats / test_validator / test_backtest_service）
- [ ] `pnpm build` → Compiled successfully，无 TypeScript 错误
- [ ] P0-1：回测历史列表可查看/筛选
- [ ] P0-2：策略参数输入有实时验证反馈
- [ ] P0-3：回测进度条实时显示百分比
- [ ] P1-1：绩效 KPI 显示 7 个指标
- [ ] P1-2：质量 KPI 显示 5 个指标
- [ ] P1-3：批量回测支持参数网格
- [ ] P1-4：多结果对比可用
- [ ] P1-5：浏览器通知 + 音频告警触发
- [ ] P1-6：权益曲线图表完整
- [ ] P1-7：交易明细可查看排序

---

## 六、阶段规划

| 阶段 | 任务编号 | 内容 | 状态 |
|------|---------|------|------|
| 第一阶段（P0+P1） | TASK-0087 | 10项功能，21文件 | 🔓 当前签发 |
| 第二阶段（P2） | TASK-0088（待建） | 6项功能，~12文件 | ⏳ Stage 1 验收后签 |
| 第三阶段（P3） | TASK-0089（待建） | 3项功能，~5文件 | ⏳ Stage 2 验收后签 |

---

## 七、关联文档

- Token 申请：[BACKTEST-WEB-Token申请-Claude.md](../handoffs/BACKTEST-WEB-Token申请-Claude.md)
- 预审：[TASK-0087-review.md](../reviews/TASK-0087-review.md)
