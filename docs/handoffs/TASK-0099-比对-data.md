# 数据端（data）功能比对：临时看板 vs v0 看板

**比对日期**：2026-04-13  
**临时看板路径**：`services/data/data_web/`  
**v0 看板路径**：`docs/portal-design/v0-close/app/data/` + `v0-close/data/`（无独立子应用）  
**后端 API**：`services/data/src/main.py` + `api/routes/data_web.py` (port 8105)

---

## 页面级对比

| 页面 | 临时看板 | v0 统一门户路由 | 差异 |
|------|---------|--------------|------|
| 首页/总览 | `app/page.tsx` ✅ SPA (6 模块) + `overview-page.tsx` | `app/data/page.tsx` 🔴 全 mock | v0 首页采集器/资源全 mock |
| 采集器管理 | `app/collections/page.tsx` + `collectors-page.tsx` ✅ **API** | `app/data/collectors/page.tsx` 🔴 mock | v0 采集器页全 mock |
| 数据浏览 | `components/pages/data-explorer-page.tsx` ✅ | `app/data/explorer/page.tsx` 🔴 mock | v0 浏览器全 mock |
| 新闻资讯 | `components/pages/news-feed-page.tsx` ✅ **API** | `app/data/news/page.tsx` 🔴 mock | v0 新闻页全 mock |
| 硬件系统 | `components/pages/system-monitor-page.tsx` ✅ **API** | `app/data/system/page.tsx` 🔴 mock | v0 系统页全 mock |
| 配置设置 | `components/pages/settings-page.tsx` ✅ | ❌ 无对应路由 | v0 缺失 |
| 操作台 | `app/operations/page.tsx` ✅ | ❌ 无 | v0 缺失 |
| 智能监控 | `app/intelligence/page.tsx` ✅ | ❌ 无 | v0 缺失 |
| Agent 网络 | `app/agent-network/page.tsx` ✅ | ❌ 无 | v0 缺失 |
| 历史 | `app/history/page.tsx` ✅ | ❌ 无 | v0 缺失 |
| 参数优化 | `app/optimizer/page.tsx` ✅ | ❌ 无 | v0 缺失 |
| 系统管理 | `app/systems/page.tsx` ✅ | ❌ 无 | v0 缺失 |
| 指挥中心 | `app/command-center/page.tsx` ✅ | ❌ 无 | v0 缺失 |

---

## 组件级功能对比

### 总览 (overview)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 采集器状态摘要 | ✅ `/api/v1/dashboard/collectors` | 🔴 mock 8 个采集器 | v0 需对接 |
| 成功/失败/延迟/空闲统计 | ✅ 从 API 聚合 | 🔴 mock 统计 | v0 需对接 |
| 硬件资源 (CPU/内存/磁盘) | ✅ `/api/v1/dashboard/system` | 🔴 mock `cpu=23,mem=45,disk=62` | v0 需对接 |
| 存储概览 | ✅ `/api/v1/dashboard/storage` | ❌ 无 | v0 缺失 |
| 日志流 | ✅ 实时显示 | 🔴 mock 5 条日志 | v0 需对接 |
| 刷新令牌 (nonce) | ✅ refreshNonce 联动 | ❌ 无 | v0 缺失 |

### 采集器管理 (collectors)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 采集器列表 | ✅ `/api/v1/dashboard/collectors` | 🔴 mock 8 条记录 | v0 需对接 |
| 采集器状态灯 | ✅ 实时状态 | 🔴 mock status | v0 需对接 |
| 重启采集器 | ✅ POST `/api/v1/ops/restart-collector` | ❌ 无操作按钮 | v0 缺失 |
| 自动修复 | ✅ POST `/api/v1/ops/auto-remediate` | ❌ 无 | v0 缺失 |
| 采集历史 | ✅ `/collection/history` | ❌ 无 | v0 缺失 |
| 采集进度 SSE | ✅ `/collection/progress/{id}/stream` | ❌ 无 | v0 缺失 |
| 数据源健康 | ✅ `/source/{id}/health` | ❌ 无 | v0 缺失 |
| 数据源验证 | ✅ POST `/source/validate` | ❌ 无 | v0 缺失 |
| 批量采集 | ✅ POST `/collection/batch` | ❌ 无 | v0 缺失 |
| 采集质量 | ✅ `/collection/{id}/quality` | ❌ 无 | v0 缺失 |

### 数据浏览 (explorer)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 品种列表 | ✅ `/api/v1/symbols` | 🔴 mock | v0 需对接 |
| K线数据查询 | ✅ `/api/v1/bars` | 🔴 mock | v0 需对接 |
| 股票K线 | ✅ `/api/v1/stocks/bars` | ❌ 无 | v0 缺失 |
| 版本信息 | ✅ `/api/v1/version` | ❌ 无 | v0 缺失 |

### 新闻资讯 (news)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 新闻列表 | ✅ `/api/v1/dashboard/news` | 🔴 mock 列表 | v0 需对接 |
| 新闻分类 | ✅ 分类筛选 | ❌ 无 | v0 缺失 |
| 新闻摘要 | ✅ summary 字段 | 🔴 mock | v0 需对接 |

### 硬件系统 (system)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| CPU 使用率 | ✅ `/api/v1/dashboard/system` | 🔴 mock 23% | v0 需对接 |
| 内存使用 | ✅ 实时 | 🔴 mock 45% | v0 需对接 |
| 磁盘使用 | ✅ 实时 | 🔴 mock 62% | v0 需对接 |
| 磁盘空间详情 | ✅ `/api/v1/dashboard/storage` | ❌ 无 | v0 缺失 |

### 数据端独特组件

| 组件 | 临时看板 | v0 看板 | 差距 |
|------|---------|--------|------|
| CollectionAnalysis | ✅ | ❌ 无 | v0 缺失 |
| CollectionHeatmap | ✅ | ❌ 无 | v0 缺失 |
| CollectionOptimizer | ✅ | ❌ 无 | v0 缺失 |
| CollectionQueue | ✅ | ❌ 无 | v0 缺失 |
| CollectionStatsChart | ✅ | ❌ 无 | v0 缺失 |
| DataQualityKPI | ✅ | ❌ 无 | v0 缺失 |
| DataSourceAnalysis | ✅ | ❌ 无 | v0 缺失 |
| DataSourceComparison | ✅ | ❌ 无 | v0 缺失 |
| DataSourceConfigEditor | ✅ | ❌ 无 | v0 缺失 |
| DataSourceHealthKPI | ✅ | ❌ 无 | v0 缺失 |
| DataSourceTemplates | ✅ | ❌ 无 | v0 缺失 |
| SourceConfigInput | ✅ | ❌ 无 | v0 缺失 |

---

## 后端 API 清单（data:8105 已有，v0 需对接）

| API | 方法 | 用途 | v0 当前状态 |
|-----|------|------|-----------|
| `/health` `/api/v1/health` | GET | 健康检查 | ❌ 未用 |
| `/api/v1/version` | GET | 版本信息 | ❌ 未用 |
| `/api/v1/symbols` | GET | 品种列表 | ❌ 未用 |
| `/api/v1/bars` | GET | K线数据 | ❌ 未用 |
| `/api/v1/stocks/bars` | GET | 股票K线 | ❌ 未用 |
| `/api/v1/dashboard/system` | GET | 系统资源 | ❌ 未用 |
| `/api/v1/dashboard/collectors` | GET | 采集器状态 | ❌ 未用 |
| `/api/v1/dashboard/storage` | GET | 存储概览 | ❌ 未用 |
| `/api/v1/dashboard/news` | GET | 新闻列表 | ❌ 未用 |
| `/api/v1/ops/restart-collector` | POST | 重启采集器 | ❌ 未用 |
| `/api/v1/ops/auto-remediate` | POST | 自动修复 | ❌ 未用 |
| `/collection/history` | GET | 采集历史 | ❌ 未用 |
| `/source/validate` | POST | 数据源验证 | ❌ 未用 |
| `/collection/progress/{id}/stream` | GET (SSE) | 采集进度流 | ❌ 未用 |
| `/collection/{id}/quality` | GET | 采集质量 | ❌ 未用 |
| `/source/{id}/health` | GET | 数据源健康 | ❌ 未用 |
| `/collection/batch` | POST | 批量采集 | ❌ 未用 |

---

## 升级要求（Claude 实施清单）

### 优先级 P0（核心链路）
1. **data/page.tsx 首页**：对接 `/api/v1/dashboard/collectors` + `/api/v1/dashboard/system`，显示采集器状态和系统资源
2. **collectors 页面**：对接 `/api/v1/dashboard/collectors`，实现重启按钮 `/api/v1/ops/restart-collector`
3. **news 页面**：对接 `/api/v1/dashboard/news`

### 优先级 P1（完善体验）
4. 系统资源 KPI：对接 `/api/v1/dashboard/system` (CPU/内存/磁盘)
5. 存储概览：对接 `/api/v1/dashboard/storage`
6. 数据浏览器：对接 `/api/v1/symbols` + `/api/v1/bars`
7. 自动修复按钮：对接 `/api/v1/ops/auto-remediate`

### 优先级 P2（增强功能 - 从临时看板回补）
8. CollectionHeatmap 采集热力图
9. DataQualityKPI 数据质量指标
10. DataSourceHealthKPI 数据源健康度
11. CollectionQueue 采集队列管理
12. CollectionStatsChart 采集统计图
13. 采集进度 SSE 流
14. 数据源验证功能
15. 批量采集功能
16. 配置设置页面

### 参考代码来源
- 临时看板 `services/data/data_web/` (无独立 lib/api 文件，直接 fetch)
- 临时看板 `components/pages/` 下 6 个页面组件
- 临时看板各业务组件（CollectionAnalysis, DataSourceHealthKPI 等）

---

## 特殊备注

数据端 v0 并没有独立子应用（不像 sim-trading/backtest/decision 有 `v0-close/{service}/` 目录），v0-close 中的 data 只有统一门户路由 `v0-close/app/data/` 下的 5 个页面。数据端临时看板功能远超 v0 设计，有 13 个页面 + 12 个业务组件。
