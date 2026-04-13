# TASK-0093 — data 看板增强 P0+P1 阶段

## 基本信息

| 字段 | 值 |
|------|----|
| 任务 ID | TASK-0093 |
| 服务 | services/data |
| 阶段 | P0+P1（核心功能 + 高优先级功能）|
| Agent | claude |
| 预审 | TASK-0093-0094-0095-review |
| 有效期 | 7 天 |

## 功能范围

- P0-1：数据采集历史记录（后端 API + 前端页面）
- P0-2：数据源配置验证（validator + 实时反馈）
- P0-3：采集进度实时推送（SSE + ProgressTracker）
- P1-1：数据质量 KPI（7 个指标）
- P1-2：数据源健康 KPI（5 个指标）
- P1-3：批量采集任务
- P1-4：数据源对比
- P1-5：实时采集告警（浏览器通知 + 音频）
- P1-6：采集统计可视化
- P1-7：数据源详情分析

## 文件白名单（25 文件）

### 后端（11 文件）
- `services/data/src/api/app.py`
- `services/data/src/api/routes/data_web.py`
- `services/data/src/data/validator.py`
- `services/data/src/data/progress_tracker.py`
- `services/data/src/stats/__init__.py`
- `services/data/src/stats/quality.py`
- `services/data/src/stats/health.py`
- `services/data/tests/test_stats.py`
- `services/data/tests/test_validator.py`
- `services/data/tests/test_data_service.py`
- `services/data/pytest.ini`

### 前端（14 文件）
- `services/data/data_web/app/history/page.tsx`
- `services/data/data_web/app/collections/page.tsx`
- `services/data/data_web/components/DataQualityKPI.tsx`
- `services/data/data_web/components/DataSourceHealthKPI.tsx`
- `services/data/data_web/components/DataSourceComparison.tsx`
- `services/data/data_web/components/CollectionStatsChart.tsx`
- `services/data/data_web/components/DataSourceAnalysis.tsx`
- `services/data/data_web/components/ProgressTracker.tsx`
- `services/data/data_web/components/SourceConfigInput.tsx`
- `services/data/data_web/lib/data-api.ts`
- `services/data/data_web/lib/notification.ts`
- `services/data/data_web/lib/audio.ts`
- `services/data/data_web/lib/keyboard.ts`
- `services/data/data_web/components/ui/label.tsx`
