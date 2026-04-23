# Atlas ↔ Alienware 交接单

> 最后更新: 2026-04-19 批次3验证收口  
> 用途: Atlas 无法通过 SSH 在 Windows 上可靠执行后台进程/PowerShell 命令，所有需要在 Alienware 本地执行的操作通过此文档交接。

---

## 当前待办（Alienware 侧执行）

### ✅ 历史已完成

| # | 事项 | 状态 |
|---|------|------|
| 1 | 3个 researcher 文件已 SCP 到位 (kline_analyzer.py, config.py, scheduler.py) | ✅ |
| 2 | tushare 包已安装 | ✅ |
| 3 | .env.researcher 已追加 TUSHARE_TOKEN | ✅ |
| 4 | start_researcher.bat 已重写（含 TUSHARE_TOKEN） | ✅ |
| 5 | 并发锁+全量采集API+交易日历 已本地修改并由 Atlas 回拉合并（commit 7e002b147） | ✅ |
| 6 | 研报推送到 Studio `/api/v1/evaluate` — Decision API 正常响应（批次3验证通过） | ✅ |

---

## 批次3 验证记录（2026-04-19，Atlas 侧已确认）

| 验证项 | 结果 | 备注 |
|--------|------|------|
| Studio Decision 容器重启健康 | ✅ | `{"status":"ok"}` |
| `GET /research/health` 端点可达 | ✅ | ResearchStore 初始化正常 |
| `POST /api/v1/evaluate` 接收研报入库 | ✅ | researcher_evaluate 路由注册生效 |
| `GET /research/latest` 返回最新研报 | ✅ | 内存+JSON双层存储正常 |
| `GET /research/macro_summary` 返回宏观摘要 | ✅ | pipeline 注入生效 |
| XGBoost 过滤器初始化无报错 | ✅ | 无训练数据时 fallback 通过 |
| Sharpe 衰减监控注册到调度器 | ✅ | strategy_monitor 无异常 |

---

## ⚡ 本轮新任务（2026-04-19，优先执行）

### 背景

Atlas 本轮对 Mini + Studio 推送了大量新代码。所有代码已 push 到 GitHub（HEAD: `7e002b147`）并通过 rsync 部署到 Mini/Studio。**Alienware 侧 researcher 现在需要同步这批新代码并重启服务。**

### 任务清单

| # | 事项 | 优先级 | 执行方式 |
|---|------|--------|---------|
| 1 | 拉取最新 scheduler.py（Mini全量接入版） | **P0** | SCP（已由 Atlas 推送，见下方） |
| 2 | 拉取最新 mini_client.py（11类+futures_minute） | **P0** | SCP（已由 Atlas 推送） |
| 3 | 重启研究员服务（使新 scheduler 生效） | **P0** | 见下方命令 |
| 4 | 验证 /run 触发正常（不报错，不卡死） | **P0** | curl 测试 |
| 5 | 验证 /crawl/full 全量采集可触发 | P1 | curl 测试 |

---

## 本轮 Atlas 已完成的工作（同步说明）

### Mini 端（`services/data/src/`）

| 文件 | 变更 |
|------|------|
| `api/routes/context_route.py` | 新增 8 个 context 端点，共 13 个 |
| `researcher/mini_client.py` | `get_context_data()` 覆盖 11 类；新增 `get_futures_minute_context(hours=2)` |
| `researcher/scheduler.py` | ① 11类+futures_minute 全量消费；② 8 展示块；③ 12字段 JSON schema；④ **阶段0.5** news_api/rss→article对象→去重→LLM分析；⑤ context 注入扩至 800 字 |
| `main.py` | `get_stock_bars` 切换读取 `stock_daily/` 目录 |

### Studio Decision 端（`services/decision/src/`）

| 文件 | 变更 |
|------|------|
| `research/research_store.py` | **新增** 研报内存+JSON双层存储 |
| `research/strategy_monitor.py` | **新增** Sharpe衰减监控+池枯竭触发 |
| `research/xgboost_signal_filter.py` | **新增** XGBoost信号过滤器 |
| `api/routes/research_query.py` | **新增** `/research/latest` `/macro_summary` `/health` 查询端点 |
| `llm/researcher_qwen3_scorer.py` | macro 专属评分规则 |
| `api/routes/researcher_evaluate.py` | 研报入库 ResearchStore |

### Alienware 端回拉（commit 7e002b147）

| 文件 | 变更 |
|------|------|
| `run_researcher_server.py` | 并发锁防重入 + `POST /crawl/full` + `GET /crawl/status` |
| `src/researcher/trading_calendar.py` | 新增（交易日历工具） |

---

## 操作命令（本轮）

### 1. 重启研究员服务

```cmd
:: Alienware 上打开 CMD
taskkill /F /IM python.exe 2>nul
cd /d C:\Users\17621\jbt\services\data
start_researcher.bat
```

### 2. 验证服务已启动

```cmd
netstat -ano | findstr 8199
:: 应有 LISTENING
```

### 3. 手动触发一次研究员分析（验证新 scheduler 正常）

```cmd
curl -X POST http://localhost:8199/run
```

### 4. 验证全量采集 API

```cmd
curl -X POST http://localhost:8199/crawl/full
:: 应返回 {"success": true, "message": "全量采集已在后台启动..."}

:: 稍等几秒后查状态
curl http://localhost:8199/crawl/status
```

### 5. 查看研究员日志

```cmd
type C:\Users\17621\jbt\services\data\researcher.log
```

---

---

## 操作手册

### 1. 检查 researcher 是否在运行

```cmd
:: 在 Alienware 打开 CMD
netstat -ano | findstr 8199
```

如果有 `LISTENING`，说明服务正常。

### 2. 如果没启动 / 需要重启

```cmd
:: 先杀旧进程
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *researcher*" 2>nul

:: 用 start_researcher.bat 启动
cd /d C:\Users\17621\jbt\services\data
start_researcher.bat
```

或者手动启动（等效于 bat 内容）：

```cmd
cd /d C:\Users\17621\jbt\services\data
set OLLAMA_URL=http://localhost:11434
set DATA_API_URL=http://192.168.31.156:8105
set DECISION_API_URL=http://192.168.31.142:8104
set TUSHARE_TOKEN=e6db4d86105126f1f6f09fe933fb4c8cca044e7f94c4168317262eba
python run_researcher_server.py
```

### 3. 验证 tushare 日K拉取

```cmd
cd /d C:\Users\17621\jbt\services\data
set TUSHARE_TOKEN=e6db4d86105126f1f6f09fe933fb4c8cca044e7f94c4168317262eba
python -c "import tushare as ts; pro=ts.pro_api(); df=pro.fut_daily(ts_code='RB2510.SHF', start_date='20260414', end_date='20260418'); print(df.head())"
```

如果返回了 K 线数据，说明 tushare Token 和网络均正常。

### 4. 查看 researcher 启动日志（排错用）

```cmd
:: 如果用了 wmic 启动，日志可能不在文件里
:: 如果直接运行 start_researcher.bat，日志在终端窗口
:: 也可以查 Windows 事件查看器或加文件日志：
cd /d C:\Users\17621\jbt\services\data
set OLLAMA_URL=http://localhost:11434
set DATA_API_URL=http://192.168.31.156:8105
set DECISION_API_URL=http://192.168.31.142:8104
set TUSHARE_TOKEN=e6db4d86105126f1f6f09fe933fb4c8cca044e7f94c4168317262eba
python run_researcher_server.py > researcher.log 2>&1
:: 然后另开一个 CMD 窗口：
type C:\Users\17621\jbt\services\data\researcher.log
```

---

## Atlas 侧待办（MacBook 远程可完成）

| # | 事项 | 状态 | 备注 |
|---|------|------|------|
| 1 | SCP pipeline.py 到 Studio Decision | ✅ | rsync 已推送 |
| 2 | 重启 Studio Decision 服务 | ✅ | 容器健康 |
| 3 | 整体功能验证（批次3） | ✅ | Decision API 全通 |

---

## 后续待办（下一批次）

### 交易所公告源修复（SHFE / DCE / CZCE）

**现状**：researcher scheduler 的 context 采集中，交易所公告（shfe_notice / dce_notice / czce_notice）抓取成功率偏低，原因是三家交易所页面结构变动导致解析失败。

| 交易所 | 当前状态 | 建议修复 |
|--------|----------|----------|
| SHFE（上期所） | 解析器对新版 `/cms/` 路径失效 | 改用 JSON API `shfe.com.cn/data/...`，或改爬新版列表页 |
| DCE（大商所） | `<table>` 结构变更，XPath 失效 | 改用 `dce.com.cn/publicweb/businessguidelines/noticeList.html` RSS 或 API |
| CZCE（郑商所） | 分页参数变动，只取到第1页 | 修正 `pageNo` 参数起始值，改为 0-based |

**建议优先级**：P2（不影响核心研判，有新闻/RSS/CFTC等备用源）  
**涉及文件**：`services/data/src/researcher/mini_client.py` — `get_context_data()` 中各交易所采集分支  
**执行方**：Atlas（MacBook 修改后 rsync 到 Mini，再 SCP 到 Alienware）

---

## 协作约定

1. **Atlas → Alienware**：Atlas 把需要在 Alienware 执行的指令写在本文档"待办"区，标注优先级。
2. **Alienware → Atlas**：用户在 Alienware 执行完毕后，把结果（成功/失败/日志）反馈给 Atlas。
3. **Atlas 不再尝试通过 SSH 在 Alienware 上执行后台进程或 PowerShell 命令**（已证实不稳定）。
4. Atlas 仍可通过 SSH 做只读检查（如 `type`、`findstr`、`tasklist`、`netstat`）。
5. 文件传输（SCP）由 Atlas 直接完成，无需交接。

---

## 路径速查

| 项目 | 路径 |
|------|------|
| 项目根 | `C:\Users\17621\jbt\` |
| researcher 源码 | `C:\Users\17621\jbt\services\data\src\researcher\` |
| 启动脚本 | `C:\Users\17621\jbt\services\data\start_researcher.bat` |
| 环境配置 | `C:\Users\17621\jbt\services\data\.env.researcher` |
| Python | 系统 Python 3.11 (`C:\Users\17621\AppData\Local\Programs\Python\Python311\`) |
