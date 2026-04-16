# TASK-0123 — 数据研究员落盘与 Mini bars 数据链路修复

【task_id】TASK-0123  
【创建时间】2026-04-16  
【创建人】Atlas  
【优先级】P0（影响研究员全链路产出）  
【服务归属】services/data（Mini + Alienware 两端）  
【状态】A0 分析建档

---

## 问题描述

用户测试发现：**数据研究员所有的工作并没有落盘**。

具体表现（来自 Livis 和 Kiro 的诊断报告）：
- Alienware 研究员服务稳定运行（11 次执行，0 错误）
- 每次生成的报告固定为 711 bytes（空模板）
- 所有报告内容：`symbols_covered=0 / articles_processed=0 / news_items=[]`
- 唯一有评级的报告置信度为 0.0
- 昨天（2026-04-15）15:00~19:00 连续 6 次失败，失败率 40%

---

## 根本原因分析（Atlas 只读诊断）

经过代码审查，确认存在 **三条独立的断点**：

### 断点 1：Mini `/api/v1/bars` 返回空数据

**位置**：`services/data/src/main.py`，`get_bars()`，L490~560

`/api/v1/bars` 端点依赖 `_resolve_symbol_frame()`，后者读取：
```
_storage_root() / MINUTE_DATA_SUBDIR / {symbol_dir} / *.parquet
```
其中：
- `_storage_root()` = `DATA_STORAGE_ROOT` 环境变量（默认为代码目录下的 `runtime/data`）
- `MINUTE_DATA_SUBDIR` = `futures_minute/1m`

**推断**：Mini Docker 容器的 `DATA_STORAGE_ROOT` 可能未正确映射到宿主机实际数据目录，导致 parquet 文件扫描为空，`bars` 返回 `[]`。

**需在 Mini 上验证**：
```bash
docker exec jbt-data-1 env | grep DATA_STORAGE_ROOT
ls -lh $DATA_STORAGE_ROOT/futures_minute/1m/ 2>/dev/null | head -10
```

---

### 断点 2：Mini 缺少 `POST /api/v1/researcher/reports` 接收端点

**位置**：`services/data/src/api/routes/researcher_route.py`

经代码审查，`researcher_route.py` 只有以下 POST 端点：
- `POST /api/v1/researcher/trigger`（手动触发研究员）
- `POST /api/v1/researcher/sources`（新增采集源）

**完全没有** `POST /api/v1/researcher/reports`——即 Alienware 研究员推送报告到 Mini 的接收端点不存在。

`scheduler._push_to_data_api()` 调用：
```python
resp = await client.post(
    ResearcherConfig.DATA_API_PUSH_URL,  # http://192.168.31.76:8105/api/v1/researcher/reports
    json=report.dict(),
    ...
)
```
Mini 接到请求后因路由不存在而返回 404 或 405，推送静默失败（下面那行 `except Exception: return False` 吞掉了错误）。

这直接导致：报告只写入 Alienware 本地，从未持久化到 Mini 的正式存储——决策端 `GET /api/v1/researcher/report/latest` 查不到任何数据。

---

### 断点 3：爬虫采集源配置文件格式不兼容

**位置**：
- `services/data/configs/researcher_sources.yaml`（已存在但格式简单）
- `services/data/src/researcher/crawler/source_registry.py`（读取逻辑）

`researcher_sources.yaml` 当前内容：
```yaml
news_sources:
  - name: "新浪财经"
    url: "https://finance.sina.com.cn/futuremarket/"
    interval: 300
```

`SourceRegistry` 期望的格式（推断需要 `source_id`、`url_pattern`、`mode`、`parser`、`market` 等字段），与当前 YAML 结构不匹配，导致 `get_active_sources("all")` 返回空列表，爬虫没有任何来源可以抓取。

---

## 修复批次规划

### 批次 A — Mini bars 数据链路验证与修复（独立可做，无前驱）

**目标**：确认 Mini `/api/v1/bars` 能返回真实 K 线数据

**需要确认的事实**（需 Jay.S 在 Mini 上执行诊断）：
1. `docker exec jbt-data-1 env | grep DATA_STORAGE_ROOT`
2. `ls -lh {DATA_STORAGE_ROOT}/futures_minute/1m/`
3. `curl "http://localhost:8105/api/v1/bars?symbol=KQ.m@SHFE.rb&start=2026-04-15T09:00:00&end=2026-04-15T15:00:00&limit=10"`

**根据诊断结果**，可能需要修改：
- `docker-compose.dev.yml` 或 `docker-compose.mac.override.yml` — 数据卷挂载路径（P0 文件，需单独 Token）
- 或者在 data 服务 `.env` 中设置正确的 `DATA_STORAGE_ROOT`

**候选文件白名单**（待诊断后冻结）：
- `services/data/src/main.py` — 若需调整默认路径解析逻辑
- Mini `.env` / `docker-compose.mac.override.yml` — 待诊断后决定

---

### 批次 B — Mini 补充 `POST /api/v1/researcher/reports` 接收端点

**目标**：让 Mini 能接收 Alienware 推送的研究报告并持久化存储

**候选文件白名单**：
- `services/data/src/api/routes/researcher_route.py` — 新增 POST /reports 端点（接收+持久化报告 JSON）
- `services/data/tests/test_researcher_api.py` — 对应测试

**端点规格**：
```
POST /api/v1/researcher/reports
Body: ResearchReport JSON
Response: {report_id, stored_path, status}
存储路径: services/data/runtime/data/researcher/reports/{YYYY-MM-DD}/{HH-MM}.json
```

**验收标准**：
- `GET /api/v1/researcher/report/latest` 在批次 B 完成后能返回非空报告
- 决策端 LLM pipeline 能读取到研究员上下文

---

### 批次 C — 爬虫采集源配置文件修复

**目标**：让 `researcher_sources.yaml` 格式与 `SourceRegistry` 期望一致，使爬虫能有数据源

**候选文件白名单**：
- `services/data/configs/researcher_sources.yaml` — 完整格式修复
- `services/data/src/researcher/crawler/source_registry.py` — 若需调整兼容旧格式

**验收标准**：
- `source_registry.get_active_sources("all")` 返回至少 2 条数据源
- 研究员每小时报告中 `crawler_stats.sources_crawled > 0`

---

## 修复优先级

```
B（接收端点）= P0，最紧急，代码明确缺失
A（bars数据）= P0，需先诊断 Mini 再决定改什么
C（爬虫源）= P1，可在 A/B 后并行
```

---

## 注意事项

1. 批次 B 涉及 `researcher_route.py`，当前 TASK-0119 的白名单中没有覆盖该文件——需要新 Token
2. 批次 A 若涉及 `docker-compose.dev.yml`，是 P0 文件，需独立预审
3. Alienware 上的研究员目前将本地报告保存在 `C:\Users\17621\jbt\services\data\runtime\researcher\reports\`；批次 B 完成后，本地文件可根据 `PUSH_RETENTION_LOCAL` 配置决定是否删除

---

## 服务边界

- 批次 A/B/C：`services/data/**`
- 若 A 涉及卷挂载：`docker-compose.mac.override.yml`（需独立评估）
- 不触及 `services/decision/**`（TASK-0122 处理）

---

## 待办

- [ ] Jay.S 在 Mini 上执行 A 批诊断命令，确认 bars 数据路径
- [ ] 项目架构师预审 A/B/C 三批白名单
- [ ] Jay.S 签发 Token
- [ ] 执行实施并验收
- [ ] 验收：研究员报告大小 > 5KB，Alienware 推送到 Mini 成功，决策端 GET /latest 有数据
