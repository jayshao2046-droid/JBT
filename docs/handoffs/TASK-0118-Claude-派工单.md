# TASK-0118 Claude 实施派工单

【派发人】Atlas  
【执行人】Claude（Sonnet 4.6）  
【日期】2026-04-15  
【Token】`tok-ac2a75fe-1bf6-45ab-baaf-8a7a590e86a3` | active | TTL 480min  
【任务单】`docs/tasks/TASK-0118-data-researcher-phi4评级与Mini推送.md`  
【预审】`docs/reviews/TASK-0118-review.md` ✅

---

## 一、任务概述

对 `services/data/` 研究员子系统进行以下 5 项改造，按 Batch A → B 顺序执行，全部完成后交回 Atlas 终审：

1. **phi4 真实 LLM 评级**：替换 `report_reviewer.py` 纯数学为 Studio phi4-reasoning:14b HTTP 调用
2. **qwen3 全中文化**：`summarizer.py` 对英文新闻标题/正文翻译后再归纳
3. **Mini 存档推送**：Mini data API 新增 POST + GET 研报端点，`scheduler.py` 推成功后删除 Alienware 本地文件
4. **研究员健康度报告**：每 2 小时飞书卡片，格式类比 data 端健康报告
5. **配置补全**：`config.py` 新增 PHI4_URL、PUSH_RETENTION_LOCAL 等

---

## 二、文件白名单（所有操作只能在这 9 个文件内）

```
services/data/src/researcher/config.py           修改
services/data/src/researcher/summarizer.py       修改
services/data/src/researcher/reporter.py         修改
services/data/src/researcher/report_reviewer.py  重写（phi4 LLM）
services/data/src/researcher/scheduler.py        修改
services/data/src/researcher/researcher_health.py 新建
services/data/src/main.py                        修改（3 个研报 API）
services/data/src/researcher_store.py            新建
services/data/tests/test_researcher_api.py       新建
```

---

## 三、环境拓扑

| 主机 | IP | 角色 | 关键端口/模型 |
|------|----|------|--------------|
| Alienware | 192.168.31.223 | 研究员生成端（Windows） | :8199 researcher, :11434 qwen3:14b |
| Studio | 192.168.31.142 | phi4 推理端（macOS） | :11434 phi4-reasoning:14b |
| Mini | 192.168.31.76 | data 存储端（macOS） | :8105 data API |
| MacBook | 本地 | 开发/代码仓库 | — |

---

## 四、Batch A 实施规格（Alienware researcher 侧）

### 4.1 config.py — 新增配置项

```python
# Studio phi4 评级
PHI4_API_URL = os.getenv("PHI4_API_URL", "http://192.168.31.142:11434/api/generate")
PHI4_MODEL = "phi4-reasoning:14b"
PHI4_TIMEOUT = 30  # 秒

# 本地文件保留策略（False = 推送成功后删除）
PUSH_RETENTION_LOCAL = False

# 健康度报告推送间隔（小时）
HEALTH_INTERVAL_HOURS = 2
```

### 4.2 summarizer.py — 新增 `_translate_to_chinese()` + 在 `summarize()` 入口调用

```python
def _translate_to_chinese(self, texts: list[str]) -> list[str]:
    """用 Alienware qwen3 将英文列表翻译为中文，失败返回原文"""
    # 判断是否含大量英文（>20% ASCII 字母）
    def is_english(t): return sum(c.isascii() and c.isalpha() for c in t) / max(len(t), 1) > 0.2
    to_translate = [t for t in texts if is_english(t)]
    if not to_translate:
        return texts
    prompt = "请将以下英文标题逐条翻译为中文，仅输出中文列表，不附解释，每行一条：\n" + "\n".join(to_translate)
    try:
        resp = self._call_ollama(prompt, timeout=20)
        translated = [l.strip() for l in resp.strip().split("\n") if l.strip()]
        if len(translated) == len(to_translate):
            result = list(texts)
            idx = 0
            for i, t in enumerate(result):
                if is_english(t):
                    result[i] = translated[idx]; idx += 1
            return result
    except Exception:
        pass
    return texts

# 在 summarize(news_items, ...) 入口：
news_titles = self._translate_to_chinese([n.get("title","") for n in news_items])
for i, n in enumerate(news_items):
    n["title"] = news_titles[i]
```

### 4.3 report_reviewer.py — 重写为 phi4 LLM 评级  

完整新实现（保留 `review_and_notify` 对外接口不变）：

```python
import json, requests, logging
from .config import PHI4_API_URL, PHI4_MODEL, PHI4_TIMEOUT
from .config import DECISION_CONFIDENCE_THRESHOLD_ACCEPT, DECISION_CONFIDENCE_THRESHOLD_WARN

logger = logging.getLogger(__name__)

class ReportReviewer:
    def __init__(self, notifier):
        self.notifier = notifier

    def _call_phi4(self, report_summary: dict) -> dict:
        """调用 Studio phi4-reasoning:14b 进行语义置信度评级"""
        prompt = f"""你是量化研究分析师。请对以下期货市场研究报告进行置信度评级。

研报摘要：
- 覆盖品种数：{report_summary.get('symbol_count', 0)}
- 新闻来源数：{report_summary.get('news_count', 0)}
- 市场研判（节选）：{report_summary.get('market_overview', '')[:300]}
- 品种趋势分布：多头={report_summary.get('bullish', 0)} 空头={report_summary.get('bearish', 0)} 中性={report_summary.get('neutral', 0)}

请根据研报的信息丰富度、逻辑一致性、多空依据充分性给出综合置信度评分（0.0~1.0）和简短理由。

输出格式（仅 JSON，不要加其他文字）：
{{"confidence": 0.72, "reason": "信息来源充分，多空逻辑清晰", "改进建议": "建议补充宏观数据交叉验证"}}"""
        payload = {"model": PHI4_MODEL, "prompt": prompt, "stream": False, "format": "json"}
        resp = requests.post(PHI4_API_URL, json=payload, timeout=PHI4_TIMEOUT)
        resp.raise_for_status()
        raw = resp.json().get("response", "{}")
        return json.loads(raw)

    def _math_fallback(self, report_data: dict) -> dict:
        """phi4 不可用时的数学降级算法"""
        symbols = report_data.get("symbols", {})
        total = len(symbols)
        if total == 0:
            return {"confidence": 0.0, "reason": "无品种数据（数学降级）", "改进建议": ""}
        news_count = sum(len(v.get("news", [])) for v in symbols.values())
        news_rel = min(1.0, news_count / max(total * 2, 1))
        confidences = [v.get("confidence", 0.5) for v in symbols.values()]
        trend_align = sum(confidences) / len(confidences)
        score = round(news_rel * 0.40 + trend_align * 0.60, 4)
        return {"confidence": score, "reason": "数学降级算法（phi4 不可达）", "改进建议": "恢复 Studio phi4 后重新评级"}

    def _build_summary(self, report_data: dict) -> dict:
        symbols = report_data.get("symbols", {})
        bullish = sum(1 for v in symbols.values() if v.get("trend") in ("上涨", "bullish", "多"))
        bearish = sum(1 for v in symbols.values() if v.get("trend") in ("下跌", "bearish", "空"))
        return {
            "symbol_count": len(symbols),
            "news_count": sum(len(v.get("news", [])) for v in symbols.values()),
            "market_overview": report_data.get("market_overview", ""),
            "bullish": bullish, "bearish": bearish, "neutral": len(symbols) - bullish - bearish,
        }

    def review_and_notify(self, report_id: str, report_data: dict) -> dict:
        """主入口：评级 + 飞书通知"""
        summary = self._build_summary(report_data)
        fallback_used = False
        try:
            result = self._call_phi4(summary)
            confidence = float(result.get("confidence", 0.5))
            reason = result.get("reason", "")
            suggestion = result.get("改进建议", "")
        except Exception as e:
            logger.warning(f"phi4 评级失败，使用数学降级: {e}")
            result = self._math_fallback(report_data)
            confidence = result["confidence"]
            reason = result["reason"]
            suggestion = result.get("改进建议", "")
            fallback_used = True

        # 分级
        if confidence >= DECISION_CONFIDENCE_THRESHOLD_ACCEPT:
            level, color, label = "🟢", "turquoise", "可采信"
        elif confidence >= DECISION_CONFIDENCE_THRESHOLD_WARN:
            level, color, label = "🟡", "yellow", "建议复核"
        else:
            level, color, label = "🔴", "orange", "建议忽略"

        tag = "（数学降级）" if fallback_used else "（phi4）"
        self.notifier.send_feishu_card(
            title=f"🔬 [{report_id}] 研报置信度评级 {level}",
            color=color,
            lines=[
                f"**评级结果**：{label} {tag}",
                f"**置信度**：{confidence:.2f}",
                f"**理由**：{reason}",
                f"**改进建议**：{suggestion or '无'}",
                f"**覆盖品种**：{summary['symbol_count']} 个",
                f"**新闻来源**：{summary['news_count']} 条",
            ]
        )
        return {"confidence": confidence, "reason": reason, "suggestion": suggestion, "fallback": fallback_used}
```

### 4.4 scheduler.py — push 后删除本地 + 健康度定时任务

在 `_push_to_data_api()` 返回成功后：
```python
if push_success and not config.PUSH_RETENTION_LOCAL:
    for path in [json_path, md_path]:
        try:
            if path and os.path.exists(path): os.remove(path)
        except Exception as e:
            logger.warning(f"删除本地研报失败: {e}")
```

在 `__init__` 中注册 2 小时健康度推送（若已有 APScheduler）：
```python
from .researcher_health import ResearcherHealth
self.health_reporter = ResearcherHealth(self.notifier, self.stats)
scheduler.add_job(self.health_reporter.send_health_card, "interval", hours=2, id="health_report")
```

### 4.5 researcher_health.py — 新建

```python
"""
研究员健康度飞书卡片，每 2 小时由 scheduler 触发。
格式类比 data 端健康报告。
"""
import datetime, requests, logging
from .daily_stats import DailyStatsTracker
from .config import PHI4_API_URL, PHI4_TIMEOUT

logger = logging.getLogger(__name__)

class ResearcherHealth:
    def __init__(self, notifier, stats: DailyStatsTracker):
        self.notifier = notifier
        self.stats = stats

    def _check_phi4(self) -> bool:
        try:
            r = requests.post(PHI4_API_URL, json={"model": "phi4-reasoning:14b", "prompt": "ping", "stream": False}, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def send_health_card(self):
        today = self.stats.get_today()
        generated = today.get("reports_generated", 0)
        failed = today.get("reports_failed", 0)
        hourly = today.get("hourly", [])

        phi4_ok = self._check_phi4()
        phi4_status = "🟢 可达" if phi4_ok else "🔴 不可达"

        # 置信度分布
        confidences = [h.get("confidence", None) for h in hourly if h.get("confidence") is not None]
        accept = sum(1 for c in confidences if c >= 0.65)
        warn = sum(1 for c in confidences if 0.40 <= c < 0.65)
        ignore = sum(1 for c in confidences if c < 0.40)

        # 颜色
        if failed > 3 or (confidences and accept / len(confidences) < 0.5):
            color = "yellow"
        else:
            color = "turquoise"

        now = datetime.datetime.now()
        next_push = (now + datetime.timedelta(hours=2)).strftime("%H:%M")

        lines = [
            f"**守护进程**　研究员 :8199 🟢　phi4(Studio) {phi4_status}",
            f"**当日研报**　已生成 {generated} 份　失败 {failed} 份",
            f"**phi4 评级分布**　🟢 可采信 {accept}　🟡 建议复核 {warn}　🔴 建议忽略 {ignore}",
        ]
        if hourly:
            last = hourly[-1]
            last_time = last.get("hour", "—")
            lines.append(f"**上次研报**　{last_time}　推送 Mini：{'✅' if last.get('push_success') else '❌'}")

        self.notifier.send_feishu_card(
            title=f"🔬 JBT 研究员健康报告 | {now.strftime('%H:%M')}",
            color=color,
            lines=lines,
            footer=f"JBT researcher | Alienware | {now.strftime('%Y-%m-%d %H:%M')} | 下次推送: {next_push}",
        )
```

---

## 五、Batch B 实施规格（Mini data API 侧）

### 5.1 researcher_store.py — 新建（路径：services/data/src/researcher_store.py）

```python
"""Mini 侧研报存储：SQLite 索引 + JSON 文件"""
import os, json, sqlite3, datetime
from pathlib import Path

STORE_ROOT = os.path.join(os.getcwd(), "runtime", "data", "researcher")
DB_PATH = os.path.join(STORE_ROOT, "researcher_reports.db")

def _ensure_dirs():
    os.makedirs(STORE_ROOT, exist_ok=True)

def _get_conn():
    _ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS researcher_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT UNIQUE NOT NULL,
        date TEXT NOT NULL,
        hour TEXT NOT NULL,
        symbol_count INTEGER DEFAULT 0,
        confidence REAL DEFAULT 0.0,
        file_path TEXT,
        stored_at TEXT NOT NULL
    )""")
    conn.commit()
    return conn

def save(report: dict) -> dict:
    """保存研报到 Mini，返回 {report_id, stored_at, file_path}"""
    _ensure_dirs()
    report_id = report.get("report_id", "")
    date = report.get("date", datetime.date.today().isoformat())
    hour = report.get("hour", "00-00")
    symbols = report.get("symbols", {})
    confidence = report.get("confidence", 0.0)
    stored_at = datetime.datetime.now().isoformat()

    # 写 JSON 文件
    day_dir = os.path.join(STORE_ROOT, "reports", date)
    os.makedirs(day_dir, exist_ok=True)
    file_path = os.path.join(day_dir, f"{hour}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 写 SQLite 索引
    with _get_conn() as conn:
        conn.execute("""INSERT OR REPLACE INTO researcher_reports
            (report_id, date, hour, symbol_count, confidence, file_path, stored_at)
            VALUES (?,?,?,?,?,?,?)""",
            (report_id, date, hour, len(symbols), confidence, file_path, stored_at))
        conn.commit()

    return {"report_id": report_id, "stored_at": stored_at, "file_path": file_path}

def get_latest(date: str | None = None) -> dict | None:
    """返回最新一份完整研报，无数据返回 None"""
    target_date = date or datetime.date.today().isoformat()
    with _get_conn() as conn:
        row = conn.execute("""SELECT file_path FROM researcher_reports
            WHERE date=? ORDER BY hour DESC LIMIT 1""", (target_date,)).fetchone()
    if not row:
        return None
    with open(row[0], encoding="utf-8") as f:
        return json.load(f)

def list_reports(date: str | None = None, limit: int = 24) -> list[dict]:
    """返回指定日期的研报摘要列表（不含完整 symbols）"""
    target_date = date or datetime.date.today().isoformat()
    with _get_conn() as conn:
        rows = conn.execute("""SELECT report_id, date, hour, symbol_count, confidence, stored_at
            FROM researcher_reports WHERE date=? ORDER BY hour DESC LIMIT ?""",
            (target_date, limit)).fetchall()
    return [{"report_id": r[0], "date": r[1], "hour": r[2], "symbol_count": r[3],
             "confidence": r[4], "stored_at": r[5]} for r in rows]
```

### 5.2 main.py — 新增 3 个研报端点

在现有 import 后添加：
```python
from researcher_store import save as rs_save, get_latest as rs_get_latest, list_reports as rs_list
```

在 `app = FastAPI(...)` 后追加：
```python
# ── 研究员研报 API ─────────────────────────────────────────
class ResearchReport(BaseModel):
    report_id: str
    date: str
    hour: str
    market_overview: str = ""
    symbols: dict = {}
    confidence: float = 0.0
    confidence_reason: str = ""

@app.post("/api/v1/researcher/reports")
def post_researcher_report(report: ResearchReport):
    result = rs_save(report.model_dump())
    return {"status": "ok", **result}

@app.get("/api/v1/researcher/report/latest")
def get_latest_report(date: str | None = None):
    data = rs_get_latest(date)
    if data is None:
        raise HTTPException(status_code=404, detail="no report found")
    return data

@app.get("/api/v1/researcher/reports")
def list_researcher_reports(date: str | None = None, limit: int = 24):
    return rs_list(date, limit)
```

### 5.3 test_researcher_api.py — 新建

```python
"""API tests for researcher report endpoints on Mini data service"""
import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import researcher_store as rs

SAMPLE = {
    "report_id": "RPT-TEST-001",
    "date": "2026-01-01",
    "hour": "15-00",
    "market_overview": "测试市场研判",
    "symbols": {"rb": {"trend": "上涨", "confidence": 0.8, "news": []}},
    "confidence": 0.72,
    "confidence_reason": "phi4 测试",
}

@pytest.fixture(autouse=True)
def patch_store(tmp_path, monkeypatch):
    monkeypatch.setattr(rs, "STORE_ROOT", str(tmp_path))
    monkeypatch.setattr(rs, "DB_PATH", str(tmp_path / "test.db"))

def test_save_returns_report_id():
    result = rs.save(SAMPLE)
    assert result["report_id"] == "RPT-TEST-001"
    assert "stored_at" in result

def test_get_latest_returns_data():
    rs.save(SAMPLE)
    data = rs.get_latest("2026-01-01")
    assert data is not None
    assert data["report_id"] == "RPT-TEST-001"

def test_get_latest_not_found():
    result = rs.get_latest("1999-01-01")
    assert result is None

def test_list_reports_returns_list():
    rs.save(SAMPLE)
    reports = rs.list_reports("2026-01-01")
    assert len(reports) == 1
    assert reports[0]["report_id"] == "RPT-TEST-001"

def test_list_reports_empty_date():
    reports = rs.list_reports("1999-12-31")
    assert reports == []

def test_save_overwrite_same_id():
    rs.save(SAMPLE)
    overwrite = {**SAMPLE, "confidence": 0.90}
    rs.save(overwrite)
    data = rs.get_latest("2026-01-01")
    assert data["confidence"] == 0.90
```

---

## 六、部署步骤（实施完成后由 Claude 执行）

```bash
# Batch A: SCP 到 Alienware
scp services/data/src/researcher/config.py alienware@192.168.31.223:/Users/17621/jbt/services/data/src/researcher/config.py
scp services/data/src/researcher/summarizer.py alienware@192.168.31.223:/Users/17621/jbt/services/data/src/researcher/summarizer.py
scp services/data/src/researcher/reporter.py alienware@192.168.31.223:/Users/17621/jbt/services/data/src/researcher/reporter.py
scp services/data/src/researcher/report_reviewer.py alienware@192.168.31.223:/Users/17621/jbt/services/data/src/researcher/report_reviewer.py
scp services/data/src/researcher/scheduler.py alienware@192.168.31.223:/Users/17621/jbt/services/data/src/researcher/scheduler.py
scp services/data/src/researcher/researcher_health.py alienware@192.168.31.223:/Users/17621/jbt/services/data/src/researcher/researcher_health.py
# 重启 Alienware researcher
ssh alienware@192.168.31.223 "taskkill /F /IM python.exe /FI \"WINDOWTITLE eq researcher\" 2>nul; cd /Users/17621/jbt && start /B python services/data/run_researcher.py"

# Batch B: SCP 到 Mini（data API）
scp services/data/src/main.py mini@192.168.31.76:~/JBT/services/data/src/main.py
scp services/data/src/researcher_store.py mini@192.168.31.76:~/JBT/services/data/src/researcher_store.py
# 重启 Mini data API
ssh mini@192.168.31.76 "cd ~/JBT && pkill -f 'uvicorn.*data' 2>/dev/null; nohup python -m uvicorn services.data.src.main:app --host 0.0.0.0 --port 8105 &"
```

---

## 七、验收清单

Claude 实施完成后，逐项自校验并在此处打勾：

- [ ] `pytest services/data/tests/test_researcher_api.py -q` ≥ 6 passed
- [ ] Mini: `GET http://192.168.31.76:8105/api/v1/researcher/report/latest` → 200（有历史数据后）
- [ ] Mini: `POST /api/v1/researcher/reports` → 接收测试负载返回 200
- [ ] Alienware: 手动触发 `POST /run` → 飞书收到研报通知（全中文）+ phi4 评级卡片
- [ ] Alienware: `runtime/researcher/reports/` 在推送成功后无残留 JSON/MD
- [ ] 飞书 2h 健康度卡片已触发（`POST /run_health` 手动验证）

---

## 八、交付规则

1. 全部完成后，SCP 部署，本地 `pytest` 通过
2. 汇报给 Atlas，等待终审
3. Atlas 终审通过后：补齐 lock 文件 + git commit + 同步 Mini/Studio
4. **未经 Atlas 终审，不独立提交，不写 lock 文件**
