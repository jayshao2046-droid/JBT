# TASK-U0-20260419-008: /api/v1/stocks/bars 增加 stock_daily 读取分支

- 任务类型: U0 单服务直修（data）
- 服务边界: services/data
- 目标文件: services/data/src/main.py
- 目标: 当 stock_minute 不可用时，/api/v1/stocks/bars 自动回退读取 stock_daily，保证股票日K可用。

## 变更范围

1. `get_stock_bars()` 增加回退分支
2. 新增 `stock_daily` 加载与标准化函数
3. 保持原有 `stock_minute` 优先级不变

## 验收标准

1. stock_minute 存在时，返回 `source_kind=stock_minute`
2. stock_minute 缺失但 stock_daily 存在时，返回 `source_kind=stock_daily`
3. 两者均缺失时，返回明确 404
