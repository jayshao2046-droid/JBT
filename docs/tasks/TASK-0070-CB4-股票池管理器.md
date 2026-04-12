# TASK-0070 — CB4 股票池管理器

【签名】Atlas
【时间】2026-04-13 10:00
【设备】MacBook
【优先级】P1
【状态】执行中

---

## 任务背景

Decision Phase C CB 股票链路中的股票池管理层。CB4 在 CB3（全A股选股引擎）的基础上，维护一个常驻 30 只的股票池，实现白天/晚间轮换机制。

## 验收标准

1. 新增 `services/decision/src/research/stock_pool.py`：
   - `StockPool` 类，内部维护常驻池（max 30）+ 候选池
   - `add(symbol, reason)` / `remove(symbol, reason)` — 手动操作
   - `rotate(new_symbols: list, remove_symbols: list)` — 批量轮换（新增20/淘汰10）
   - `get_pool()` — 返回当前30只含入池时间和入池理由
   - `get_history()` — 返回淘汰记录（symbol + 淘汰理由 + 时间）
   - 持久化到 JSON 文件（路径从 env 读取）

2. 新增 `services/decision/src/api/routes/stock_pool.py`：
   - `GET /api/v1/stock/pool` — 获取当前股票池
   - `POST /api/v1/stock/pool/rotate` — 触发一次轮换（body: {add: [], remove: []}）
   - `GET /api/v1/stock/pool/history` — 获取淘汰历史

3. 更新 `services/decision/src/api/routes/__init__.py`：注册 stock_pool 路由

4. 新增 `services/decision/tests/test_stock_pool.py`：≥ 12 个测试用例

## 文件白名单

- `services/decision/src/research/stock_pool.py`（新建）
- `services/decision/src/api/routes/stock_pool.py`（新建）
- `services/decision/src/api/routes/__init__.py`（更新）
- `services/decision/tests/test_stock_pool.py`（新建）

## 依赖

- CB3 `stock_screener.py` ✅（已完成 TASK-0062）
- CB1 `stock_templates.py` ✅（已完成 TASK-0069）

## 执行 Agent

Claude-Code
Token: tok-938f517e-9047-4576-9351-0dcff9976a55（TTL 180分钟）
