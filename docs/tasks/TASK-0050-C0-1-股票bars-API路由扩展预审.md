# TASK-0050 — C0-1 股票 bars API 路由扩展

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0050 |
| 任务名称 | C0-1 股票 bars API 路由扩展 |
| 所属阶段 | Phase C / Lane-A |
| 主责服务 | `services/data/` |
| 协同服务 | `services/decision/`（消费端） |
| 优先级 | P1 |
| 状态 | 🔓 Token 已签发（tok-b7358d64） |

## 任务背景

数据服务当前（`services/data/src/main.py`）仅支持期货分钟 K 线查询路由。  
Phase C 决策双沙箱（CA/CB 链）和 CG 人工回测均需要消费股票 bars 数据，  
当前无对应 API 端点，是 CB5、C0-2、CA2'、CB2' 等任务的前置解锁项。

## 实现范围（最小白名单 — 预审调整后）

> **预审裁定（REVIEW-TASK-0050-0055-PRE）：**  
> 数据服务无 `api/` 目录，所有路由定义在 `main.py` 中；不创建 api/ 子目录，  
> 直接在 main.py 内新增股票 bars 路由。白名单缩减为 2 项。

### 修改文件

| 文件路径 | 变更摘要 |
|----------|---------|
| `services/data/src/main.py` | 新增股票 bars 查询路由，不改动其他路由 |

### 新建文件

| 文件路径 | 说明 |
|----------|------|
| `tests/data/api/test_stock_bars.py` | 股票 bars 路由单元测试 |

### 禁区（不得触及）

- `shared/contracts/**`
- `shared/python-common/**`
- `.github/**`
- `docker-compose.dev.yml`
- 任一真实 `.env`
- `services/data/src/collectors/**`（采集逻辑不在此任务范围）

## 接口需求（初版）

```
GET /api/v1/stocks/bars
  参数: symbol (str), start (date), end (date), period (str, 默认 "1d")
  返回: { symbol, period, bars: [{datetime, open, high, low, close, volume}] }
  数据源: 已存在的 stock_minute 存储目录
```

## 验收标准

1. `GET /api/v1/stocks/bars?symbol=000001.SZ&start=2025-01-01&end=2025-01-10` 返回正确 JSON。
2. symbol 不存在时返回 404，非法参数返回 422。
3. 所有新文件均有单元测试覆盖（happy path + 边界）。
4. `main.py` 无逻辑回归（原有期货路由正常响应）。
5. 无跨服务 import，无硬编码路径，无 `.env` 内读取。

## 依赖关系

- 无前置任务依赖（Lane-A 首发）
- 解锁：CB5 / C0-2 / CA2' / CB2' 均等待本任务完成

## 派发目标

**架构师预审 → Token 签发 → 数据服务 Agent 实施**

---
状态历史：  
- 2026-04-11 Atlas 建档，等待架构师预审
- 2026-04-12 架构师预审通过（REVIEW-TASK-0050-0055-PRE），白名单调整为 2 项
- 2026-04-12 Token 签发 tok-b7358d64（数据 Agent，2 文件，30min）
