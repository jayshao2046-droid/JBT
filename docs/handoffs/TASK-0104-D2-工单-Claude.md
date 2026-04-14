# TASK-0104-D2 工单 — decision 侧上下文注入（Claude-Code 执行）

> 本工单在 D1（data 侧）验收通过后方可开始。

---

## Token 信息

- **Token ID**：`tok-54f501ef-db44-404d-8fc5-ab5d81c99685`
- **Agent**：`Claude-Code`（check_token_access 时 agent 字段必须用这个，不能用其他名称）
- **任务**：`TASK-0104`

## 白名单（4 个文件，注意路径必须与 check_token_access 完全一致）

```
services/decision/src/llm/context_loader.py   ← 新建
services/decision/src/llm/pipeline.py          ← 修改
services/decision/src/llm/prompts.py           ← 修改
services/decision/tests/test_llm_context.py   ← 新建
```

## check_token_access 调用参数（精确）

```json
{
  "task_id": "TASK-0104",
  "agent": "Claude-Code",
  "action": "write",
  "files": [
    "services/decision/src/llm/context_loader.py",
    "services/decision/src/llm/pipeline.py",
    "services/decision/src/llm/prompts.py",
    "services/decision/tests/test_llm_context.py"
  ]
}
```

---

## D2 实现要求

### 1. `context_loader.py`（新建）

路径：`services/decision/src/llm/context_loader.py`

实现一个 `DailyContextLoader` 类：

```python
import os
import time
import httpx
from typing import Optional, Dict

class DailyContextLoader:
    TTL_SECONDS = 8 * 3600  # 8 小时缓存
    DATA_API_URL = os.getenv("DATA_API_URL", "http://localhost:8105")

    def __init__(self):
        self._cache: Optional[Dict] = None
        self._loaded_at: float = 0.0

    def get(self) -> Optional[Dict]:
        """返回今日预读上下文，TTL 内走内存缓存；不可用时返回 None（降级）。"""
        if self._cache and (time.time() - self._loaded_at) < self.TTL_SECONDS:
            return self._cache
        return self._refresh()

    def _refresh(self) -> Optional[Dict]:
        try:
            resp = httpx.get(
                f"{self.DATA_API_URL}/api/v1/context/daily",
                timeout=5.0
            )
            if resp.status_code == 200:
                self._cache = resp.json()
                self._loaded_at = time.time()
                return self._cache
        except Exception:
            pass
        return None  # 降级：data 不可用时不影响 LLM 调用

_loader = DailyContextLoader()

def get_daily_context() -> Optional[Dict]:
    """模块级单例访问入口。"""
    return _loader.get()
```

关键约束：
- **不可用时必须返回 None，LLM 调用不得因此中断**
- `DATA_API_URL` 通过 env 注入，默认 `http://localhost:8105`
- TTL=8h，不要用文件缓存，纯内存即可
- 不引入 asyncio（decision pipeline 是同步调用链）

### 2. `pipeline.py`（修改）

路径：`services/decision/src/llm/pipeline.py`

在 `LLMPipeline` 的三个方法中注入上下文：

```python
from src.llm.context_loader import get_daily_context

class LLMPipeline:
    def research(self, intent: str) -> str:
        ctx = get_daily_context()
        context_block = ""
        if ctx:
            researcher_ctx = ctx.get("researcher_context", {})
            if researcher_ctx:
                context_block = f"\n\n[今日市场预读]\n{researcher_ctx}\n"
        # 将 context_block 拼接到 messages 的 user content 前
        # 保持现有 messages 结构不变，只在 intent 前增加可选上下文

    def audit(self, code: str) -> str:
        ctx = get_daily_context()
        context_block = ""
        if ctx:
            audit_ctx = ctx.get("l2_audit_context", {})
            l1_brief = ctx.get("l1_briefing", {})
            if audit_ctx or l1_brief:
                context_block = f"\n\n[今日审核参考]\nL1速报: {l1_brief}\nL2上下文: {audit_ctx}\n"
        # 拼接到 code 前

    def analyze(self, performance_data: dict) -> str:
        ctx = get_daily_context()
        context_block = ""
        if ctx:
            analyst_data = ctx.get("analyst_dataset", {})
            if analyst_data:
                context_block = f"\n\n[今日分析师数据集]\n{analyst_data}\n"
        # 拼接到 performance_data 描述前
```

关键约束：
- **ctx 为 None 时走原有逻辑，不改任何现有行为**
- 只在 user message 的 content 前增加可选的 context_block
- 不改原有参数签名
- 不改模型选择逻辑

### 3. `prompts.py`（修改）

路径：`services/decision/src/llm/prompts.py`

在 `RESEARCHER_SYSTEM`、`AUDITOR_SYSTEM`、`ANALYST_SYSTEM` 三个模板中各增加一个可选 `{context}` 占位符的说明注释，让 pipeline.py 知道上下文注入点：

```python
# 研究员系统 prompt（deepcoder:14b）
# 上下文注入点：pipeline.research() 在 user message 前拼接 researcher_context
RESEARCHER_SYSTEM = """...(保持现有内容不变)..."""

# 审核员系统 prompt（qwen3:14b）
# 上下文注入点：pipeline.audit() 在 user message 前拼接 l2_audit_context + l1_briefing
AUDITOR_SYSTEM = """...(保持现有内容不变)..."""

# 数据分析师系统 prompt（phi4-reasoning:14b）
# 上下文注入点：pipeline.analyze() 在 user message 前拼接 analyst_dataset
ANALYST_SYSTEM = """...(保持现有内容不变)..."""
```

关键约束：
- **不改任何现有 prompt 文本内容**，只加注释
- 不引入模板变量替换，上下文拼接在 pipeline.py 中完成

### 4. `test_llm_context.py`（新建）

路径：`services/decision/tests/test_llm_context.py`

覆盖以下场景：

```python
def test_context_loader_returns_none_when_data_unavailable():
    """data 服务不可用时，get_daily_context() 应返回 None，不抛异常。"""
    # Mock httpx 返回 ConnectionError

def test_context_loader_caches_within_ttl():
    """TTL 内第二次调用不发 HTTP 请求，直接返回缓存。"""
    # Mock httpx 第一次返回有效数据，第二次不应被调用

def test_context_loader_refreshes_after_ttl():
    """TTL 过期后强制刷新。"""
    # Patch _loaded_at 为过去时间

def test_pipeline_research_with_context(mock_ollama):
    """有上下文时，LLM 调用的 messages 中包含 researcher_context。"""

def test_pipeline_research_without_context(mock_ollama):
    """无上下文（ctx=None）时，LLM 调用行为与原有一致。"""

def test_pipeline_audit_without_context(mock_ollama):
    """无上下文时，audit() 行为不变。"""
```

关键约束：
- `pytest services/decision/tests/test_llm_context.py -q` 全部通过
- mock httpx，不真实调用 data API
- mock Ollama HTTP 端点，不真实调用 LLM

---

## 验收标准

| 项目 | 要求 |
|------|------|
| `pytest services/decision/tests/test_llm_context.py -q` | 全部通过 |
| data API 不可用时 `LLMPipeline.research(intent)` | 无异常，正常返回 |
| data API 可用时 `LLMPipeline.research(intent)` | messages 中包含 researcher_context 片段 |
| `DATA_API_URL` 默认值 | `http://localhost:8105`（对应 Mini 本地端口）|
| 白名单外文件 | 0 修改 |

---

## 关键提醒

1. **check_token_access 必须用 `agent: "Claude-Code"`**，不能是其他名称
2. **路径严格按白名单**，不含 `src/api/` 子目录前缀
3. D2 是纯 Python 服务端修改，不涉及任何前端文件
4. 完成后向 Atlas 汇报，等待 Atlas 复核 → 项目架构师终审 → lockback

---

## 工单创建时间

2026-04-15，Atlas 预备，待 D1 完成后立即发送给 Claude-Code。
