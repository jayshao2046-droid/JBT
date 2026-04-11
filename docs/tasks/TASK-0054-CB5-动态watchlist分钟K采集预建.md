# TASK-0054 — CB5 动态 watchlist 分钟K采集

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  
【状态】📋 预建档案（等待 TASK-0050 / C0-1 完成后激活）

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0054 |
| 任务名称 | CB5 动态 watchlist 分钟K采集 |
| 所属阶段 | Phase C / Lane-B |
| 主责服务 | `services/data/` |
| 协同服务 | `services/decision/`（提供 watchlist，消费采集结果）|
| 优先级 | P1 |
| 前置依赖 | **TASK-0050（C0-1）完成**（需项目架构师预审 + Token）|
| 状态 | 📋 预建，未激活 |

## 激活条件

当 TASK-0050 经过架构师终审并由 Jay.S 确认上线后，本任务自动激活。  
**注意**：CB5 是跨服务任务，需独立申请架构师预审 + Token（与 C0-1 Token 不同）。

## 任务背景

当前 `stock_minute_collector.py` 采用静态配置的股票列表，  
CB5 目标是使采集列表动态化：由决策服务的 watchlist 驱动，  
只采集当前 watchlist 中的股票分钟 K 线，并写入 `stock_minute/` 目录（C0-1 已暴露读取接口）。

## 实现范围（最小白名单草案，待架构师确认）

### 修改文件

| 文件路径 | 变更摘要 |
|----------|---------|
| `services/data/src/collectors/stock_minute_collector.py` | 增加从 watchlist 接口动态读取 symbol 列表的逻辑 |
| `services/data/src/scheduler/pipeline.py` | 为 watchlist 采集任务配置调度规则 |

### 新建文件

| 文件路径 | 说明 |
|----------|------|
| `services/data/src/collectors/watchlist_client.py` | 调用决策服务 watchlist API 的 HTTP 客户端 |
| `tests/data/collectors/test_watchlist_client.py` | 测试文件 |

### 禁区

- `shared/contracts/**`、`shared/python-common/**`
- `.github/**`、`docker-compose.dev.yml`、任一真实 `.env`
- `services/decision/**`（watchlist API 由决策服务自行维护）

## 跨服务门禁说明

CB5 通过 HTTP 调用决策服务 watchlist 端点，**不得直接 import 决策服务代码**。  
若 watchlist API 尚未定义，需先在 `shared/contracts` 登记（由架构师主导）。

## 验收标准（草案）

1. 调度触发时，`stock_minute_collector.py` 从决策服务获取 watchlist 并仅采集列表内股票。
2. 决策服务不可达时，降级到上次缓存的 watchlist（不崩溃）。
3. 采集结果写入 `stock_minute/` 目录，格式与现有 stock_minute 数据一致。
4. 单元测试：mock 决策服务响应，验证采集 symbol 列表正确。

## 依赖关系

- 前置：C0-1（stock_minute 读取接口已稳定）
- 解锁：CB6（盘中跟踪与飞书通知）

---

状态历史：  
- 2026-04-11 Atlas 预建档案，等待 C0-1 完成 + Token 签发后激活
