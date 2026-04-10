# TASK-0036 data端 U0 外盘分钟K线 0产出修复

## 文档信息

- 任务 ID：TASK-0036
- 文档类型：单服务 U0 事后审计
- 签名：Atlas
- 建档时间：2026-04-10 13:15
- 设备：MacBook
- 关联提交：`300c77d`

---

## 一、任务来源

1. 本任务来源于 Jay.S 观察到飞书持续推送"外盘分钟K线(yfinance) 0产出"通知（截图确认：`0 条 | 78.1s` 与 `0 条 | 2.1s`），要求排查并修复。
2. 属于 data 单服务运行态排障，Jay.S 明确 U0 直修指令。

---

## 二、U0 适用性确认

1. 直修全程仅限 `services/data/src/collectors/` 与 `services/data/src/scheduler/` 两个子目录，共 2 个文件。
2. 未触碰永久禁区：`shared/contracts/**`、`shared/python-common/**`、`WORKFLOW.md`、`.github/**`、`docker-compose.dev.yml`、任一 `.env.example`、任一真实 `.env`、`runtime/**`、`logs/**`。
3. 无跨服务写入、无目录新增、无 shared 代码改动、无部署编排改动。
4. 用户已确认运行态验证成功（25/27 品种成功，24861 bars），符合 U0 成功后一次性补齐审计材料的收口条件。

---

## 三、只读排查过程

| 步骤 | 发现 |
|------|------|
| 查看 Mini 进程和日志 | 调度器 PID 82065 运行，日志文件全空（stdout→/dev/null） |
| 检查 vpn.yaml | Mini 无 `vpn.yaml`，但代理 `127.0.0.1:7890` 实际连通（204 OK） |
| 手动测试 `Ticker('GC=F').history(period='5d', interval='1m')` | 返回 0 行，报 "possibly delisted; no price data found"；耗时 15.7s |
| 手动测试 `download(period='5d')` | `YFRateLimitError: Too Many Requests`（偶发，代理 IP 轮换后恢复） |
| 测试 `period='2d' + auto_adjust=True` | CL=F 返回 1433 行 ✅ |
| 5品种批量测试 | GC/SI/ES/NQ/ZC 全部成功，ok=5 fail=0，4.8s |

---

## 四、实际直修范围

| 文件 | 改动摘要 |
|------|---------|
| `services/data/src/collectors/overseas_minute_collector.py` | `Ticker.history()` 加 `auto_adjust=True`；`sleep(0.3)` → `sleep(0.5)` 减少并发压力；异常检测补充 `ratelimit` 关键词 |
| `services/data/src/scheduler/pipeline.py` | `collector.collect(period="1d", ...)` → `period="2d"` 确保非交易时段返回近两日数据 |

---

## 五、根本原因分析

| 根因 | 原因详情 |
|------|---------|
| `period="1d"` 空数据 | 采集执行时为北京时间 12:44（美东凌晨 0:44），当日美股尚未开盘，`1d` 返回空 |
| 缺 `auto_adjust=True` | yfinance 0.2.54 下 `Ticker.history()` 缺该参数返回 "possibly delisted"，非真实下市 |
| `sleep(0.3)` 过短 | 27 品种逐一请求，高频触发 Yahoo Finance IP 限流（`YFRateLimitError`）|

---

## 六、运行态验证摘要

| 验证项 | 结果 |
|--------|------|
| 手动触发 `run_overseas_minute_yf_pipeline()` | 25/27 品种成功，24861 bars written，39.7s ✅ |
| 剩余 2 个失败品种 | `CT=F`（棉花）、`RS=F`（油菜籽）Yahoo Finance 无此合约，属已知限制 |
| Mini 调度器重启 PID | 82627 ✅ |
| Git 提交推送 | `300c77d` → `origin main` ✅ |
| Mini 两地源码同步 | rsync collectors + pipeline 文件一致 ✅ |

---

## 七、明确排除

1. `CT=F`/`RS=F` 2个 ticker 不在 Yahoo Finance，需另起任务决定备源（AkShare/Twelve Data）。
2. 不修改 `ALPHA_VANTAGE_API_KEY` / `TWELVE_DATA_API_KEY` 配置，不修改备源逻辑。
3. 不修改 `vpn.yaml` 缺失问题，当前代理直连已稳定工作。
4. 本任务只负责补齐审计账本与远端备份，不追加新业务修复。

---

## 八、验收标准

1. 飞书资讯群外盘分钟通知显示非零产出（25 条或以上）。✅（手动验证通过）
2. Git 提交 `300c77d` 推送至 `origin main`。✅
3. Mini 两地文件同步一致。✅
4. TASK-0036 task/review/lock/handoff 四类账本补齐。✅
5. Atlas prompt 追加 TASK-0036 动作日志。✅
