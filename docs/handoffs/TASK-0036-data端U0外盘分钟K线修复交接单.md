# HANDOFF-TASK-0036 data端 U0 外盘分钟K线 0产出修复

## 文档信息

- 任务 ID：TASK-0036
- 交接类型：U0 事后审计收口
- 签名：Atlas
- 时间：2026-04-10 13:15
- 设备：MacBook

---

## 一、修复问题清单

| # | 问题 | 修复文件 | 改动 |
|---|------|---------|------|
| 1 | `period="1d"` 亚洲时段返回空 | `pipeline.py` | → `period="2d"` |
| 2 | 缺 `auto_adjust=True` 导致 "possibly delisted" | `overseas_minute_collector.py` | 加参数 |
| 3 | `sleep(0.3)` 触发 Yahoo 限流 | `overseas_minute_collector.py` | → `sleep(0.5)` |

---

## 二、已知限制（不在本次范围）

- `ICE.CT` (`CT=F` 棉花) 和 `ICE.RS` (`RS=F` 油菜籽) 在 Yahoo Finance 无数据，属平台限制。
- 若需补齐，可选方案：Twelve Data（`ICE.CT` 支持）或 AkShare 日线降级。

---

## 三、运行态状态

- Mini 调度器：PID 82627，每5分钟采集一次（仅外盘交易时段）
- 采集成功率：25/27（92.6%）
- Git：`300c77d` → origin main

---

## 四、接口与部署说明

- Mini data 服务：`jaybot@172.16.0.49:~/JBT/`（蒲公英 172.16.0.49）
- 重启调度器：`ssh jaybot@172.16.0.49 'cd ~/JBT && pkill -f data_scheduler; nohup .venv/bin/python -m services.data.src.scheduler.data_scheduler --daemon > /dev/null 2>&1 &'`
- 手动触发外盘采集测试：
  ```python
  from services.data.src.scheduler.pipeline import run_overseas_minute_yf_pipeline
  result = run_overseas_minute_yf_pipeline()
  print(sum(result.values()), "bars,", len(result), "symbols")
  ```

---

## 五、后继注意事项

1. yfinance 需要代理 `127.0.0.1:7890`，如代理变更须同步修改 `services/data/configs/vpn.yaml`。
2. `period="2d"` 会多拉一天历史，`_save_records` 会处理重复写入，不影响数据一致性。
3. Yahoo Finance 会偶发限流，`_backoff_state` 退避机制自动处理，无需人工干预。

---

## 六、关联文档

- 任务：`docs/tasks/TASK-0036-data端U0外盘分钟K线0产出修复.md`
- 审查：`docs/reviews/TASK-0036-review.md`
- 锁回：`docs/locks/TASK-0036-lock.md`
- 前情：`TASK-0035`（data端U0新闻卡片排版与推送路由修复）
