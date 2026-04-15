# TASK-0118 研究员报告 phi4 评级 + Mini 推送存档 + 健康度报告 + 全中文化

【建档】Atlas  
【日期】2026-04-15  
【状态】active — Token 已签发，等待 Claude 执行

## 1. 背景与动机

当前研报生成链路存在以下问题：

| 问题 | 当前状态 | 目标状态 |
|------|----------|----------|
| 置信度评分 | 纯数学（非 LLM） | Studio phi4-reasoning:14b 语义真实推理 |
| 研报存储 | 残留 Alienware 本地 | 仅推送 Mini，Alienware 不保留文件 |
| 决策端拉取研报 | `/api/v1/researcher/report/latest` 404 | Mini data API 实现，决策端正常拉取 |
| 研报语言 | 中英混杂（新闻标题/分析可能含英文） | 强制全中文，qwen3 翻译所有英文内容 |
| 研究员健康度 | 无定期汇报 | 每 2 小时飞书卡片，格式类比 data 端健康报告 |

## 2. 服务边界

- 本任务仅涉及 `services/data/` 单服务
- Alienware 负责生成与推送（researcher 进程）
- Mini 负责存储与供数（data API :8105）
- Studio phi4 通过 HTTP 提供评级（192.168.31.142:11434）

## 3. 文件白名单（按批次）

### Batch A — Alienware researcher 侧（6 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/researcher/summarizer.py` | 修改 | 新增 `_translate_to_chinese()` — qwen3 翻译全部英文新闻标题/正文后才归纳 |
| `services/data/src/researcher/reporter.py` | 修改 | 报告所有字段强制中文；移除写本地文件（或写完后 push 然后删除） |
| `services/data/src/researcher/report_reviewer.py` | 重写 | 替换纯数学为 phi4 HTTP 调用（Studio 192.168.31.142:11434），保留数学作为 fallback |
| `services/data/src/researcher/scheduler.py` | 修改 | push_to_mini → 成功后删除 Alienware 本地 JSON/MD；push 失败持久化重试2次 |
| `services/data/src/researcher/researcher_health.py` | 新建 | 每2小时飞书通知：启动次数/总研报数/失败数/本轮品种覆盖/phi4评级分布/上次推送时间 |
| `services/data/src/researcher/config.py` | 修改 | 新增 `PHI4_URL`（Studio Ollama）、`PUSH_RETENTION_LOCAL`=False、`HEALTH_INTERVAL_HOURS`=2 |

### Batch B — Mini data API 侧（3 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/data/src/main.py` | 修改 | 新增 `POST /api/v1/researcher/reports`、`GET /api/v1/researcher/report/latest`、`GET /api/v1/researcher/reports` |
| `services/data/src/researcher_store.py` | 新建 | Mini 侧研报存储：SQLite `researcher_reports`表 + 文件存档（`runtime/data/researcher/`） |
| `services/data/tests/test_researcher_api.py` | 新建 | 测试三个端点 CRUD（最少 6 个 test） |

## 4. 技术规格

### 4.1 phi4 评级（Batch A - report_reviewer.py）

```
POST http://192.168.31.142:11434/api/generate
model: phi4-reasoning:14b
prompt: 中文，包含研报摘要（市场研判/品种趋势分布/新闻相关性）
输出：JSON { "confidence": 0.0~1.0, "reason": "...", "改进建议": "..." }
超时：30s；失败时 fallback 到数学算法（不中断主流程）
```

分级：≥0.65 → 🟢 可采信；0.40-0.64 → 🟡 建议复核；<0.40 → 🔴 建议忽略

### 4.2 qwen3 翻译（Batch A - summarizer.py）

- 在 `_build_prompt()` 之前，调 Alienware qwen3 翻译所有英文 news_items
- 翻译 prompt 精简：`"请将以下英文标题逐条翻译为中文，仅输出中文列表，不附解释：\n{items}"`
- 单次最多翻译 10 条；超时 20s；失败保留原文

### 4.3 Mini 研报 API（Batch B - main.py）

```
POST /api/v1/researcher/reports
  Body: ResearchReport JSON（Alienware 推送）
  → researcher_store.save(report); 返回 {report_id, stored_at}

GET /api/v1/researcher/report/latest?date=YYYY-MM-DD
  → 返回最新一份完整研报 JSON
  → 无参数时返回当日最新，无数据返回 404

GET /api/v1/researcher/reports?date=YYYY-MM-DD&limit=24
  → 返回指定日期研报列表（摘要，不含完整 symbols）
```

### 4.4 研究员健康度报告（Batch A - researcher_health.py）

每 2 小时由 scheduler 触发，飞书 `turquoise` 通知卡片：

```
🔬 [JBT 研究员-健康度] YYYY-MM-DD HH:00

守护进程
  研究员进程  ● 运行中 / ● 已停止

当日研报统计
  已生成: N 份     失败: N 份
  覆盖品种: N 个
  总字节: XX KB

phi4 评级分布
  🟢 可采信: N 份   🟡 建议复核: N 份   🔴 建议忽略: N 份

上次研报推送: HH:MM (N分钟前)
上次推送 Mini: ✅ 成功 / ❌ 失败
```

颜色规则：全天失败数 > 3 → `orange`；phi4可采信率 < 50% → `yellow`；其余 `turquoise`

### 4.5 Alienware 不保留研报（scheduler.py）

```python
# push 成功后删除本地
if push_success:
    os.remove(json_path)
    os.remove(md_path)
# push 失败：保留本地，记入 daily_stats.push_failed，下次循环重试（最多2次）
```

## 5. 验收标准

1. `pytest services/data/tests/test_researcher_api.py -q` ≥ 6 passed
2. 手动触发 `POST /run` → 飞书收到研报通知 + phi4 评级卡片（均为中文）
3. `GET http://192.168.31.76:8105/api/v1/researcher/report/latest` 返回 200 + 完整 JSON
4. `GET http://192.168.31.76:8105/api/v1/researcher/reports?date=今日` 返回非空列表
5. Alienware 本地 `runtime/researcher/reports/` 在推送成功后不留 JSON/MD 文件
6. 2 小时健康度飞书卡片正常推送（可 POST /run_health 手动触发验证）

## 6. 回滚方案

- Batch A 失败：恢复 `report_reviewer.py`（数学算法）、`reporter.py`（含本地写入）
- Batch B 失败：移除 main.py 中三个路由，不影响 data 服务其他功能
- Git 回滚锚点：执行后标注 commit SHA

## 7. 执行顺序

A → B 顺序执行；Batch A 内部：`config.py` → `summarizer.py` → `reporter.py` → `report_reviewer.py` → `scheduler.py` → `researcher_health.py`（新建）；Batch B 内部：`researcher_store.py`（新建）→ `main.py` → `tests`
