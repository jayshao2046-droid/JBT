# TASK-0094 — data 看板增强 P2 阶段

## 基本信息

| 字段 | 值 |
|------|----|
| 任务 ID | TASK-0094 |
| 服务 | services/data |
| 阶段 | P2（中优先级功能）|
| Agent | claude |
| 预审 | TASK-0093-0094-0095-review |
| 有效期 | 5 天 |

## 功能范围

- P2-1：数据采集分析增强（月度热力图 + 年度数据量对比）
- P2-2：采集参数优化器（网格搜索 + 自动调优）
- P2-3：数据源配置可视化编辑
- P2-4：采集任务队列管理
- P2-5：数据源模板功能
- P2-6：多时间框架分析

## 文件白名单（14 文件）

### 后端（6 文件）
- `services/data/src/api/app.py`
- `services/data/src/stats/optimizer.py`
- `services/data/src/queue/__init__.py`
- `services/data/src/queue/manager.py`
- `services/data/tests/test_optimizer.py`
- `services/data/tests/test_queue.py`

### 前端（8 文件）
- `services/data/data_web/app/optimizer/page.tsx`
- `services/data/data_web/components/CollectionAnalysis.tsx`
- `services/data/data_web/components/CollectionOptimizer.tsx`
- `services/data/data_web/components/DataSourceConfigEditor.tsx`
- `services/data/data_web/components/CollectionQueue.tsx`
- `services/data/data_web/components/DataSourceTemplates.tsx`
- `services/data/data_web/lib/data-api.ts`
- `services/data/data_web/lib/keyboard.ts`
