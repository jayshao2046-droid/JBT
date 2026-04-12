# Claude 派发单 — TASK-0081 CF1' LLM Pipeline

## 你要做什么

在 decision 服务中新增一个 `llm/` 模块，实现 **Ollama 三模型串行调用流水线**。

三个模型部署在 Studio（192.168.31.142:11434），通过 HTTP 调用，不是本地加载：

| 模型 | 角色 | 用途 |
|------|------|------|
| `deepcoder:14b` | 策略研究员 | 接收策略意图描述，生成策略 Python 代码 |
| `qwen3:14b` | 审核员 | 接收策略代码，做逻辑校验和风险审核 |
| `phi4-reasoning:14b` | 数据分析师 | 接收绩效数据，做归因分析和改进建议 |

**关键约束**：Studio 只有 32GB 内存，三个模型不能同时驻留。每次调用必须带 `keep_alive: 0`（响应完成后立即卸载模型）。

---

## Token

- **Token ID**: `tok-c3287270-8903-48b8-82f9-9d2b8e4e241e`
- **任务**: TASK-0081
- **有效期**: 480 分钟

## 白名单（7 个文件）

| 操作 | 文件路径 |
|------|---------|
| 新建 | `services/decision/src/llm/__init__.py` |
| 新建 | `services/decision/src/llm/client.py` |
| 新建 | `services/decision/src/llm/pipeline.py` |
| 新建 | `services/decision/src/llm/prompts.py` |
| 新建 | `services/decision/src/api/routes/llm.py` |
| 新建 | `services/decision/tests/test_llm_pipeline.py` |
| 修改 | `services/decision/src/api/app.py` |

---

## 文件 1：`services/decision/src/llm/__init__.py`

空 init 文件。

---

## 文件 2：`services/decision/src/llm/client.py`

Ollama HTTP 客户端，封装底层调用。

```python
class OllamaClient:
    def __init__(self, base_url: str = "http://192.168.31.142:11434"):
        ...

    async def chat(self, model: str, messages: list[dict], timeout: float = 300.0) -> dict:
        """
        调用 Ollama /api/chat 端点。
        - stream=False（同步返回完整结果）
        - keep_alive=0（响应后立即卸载模型，防止 OOM）
        - 超时 300 秒
        - 返回 dict 包含 content, model, total_duration, eval_count, eval_duration
        """
```

要求：
- 使用 `httpx.AsyncClient`（decision 已依赖 httpx）
- base_url 从环境变量 `OLLAMA_BASE_URL` 读取，默认 `http://192.168.31.142:11434`
- 请求体固定 `"stream": false, "keep_alive": 0`
- 超时处理：httpx.TimeoutException → 返回带 error 字段的 dict，不抛异常
- 添加 `async def list_models(self)` 方法（调用 GET /api/tags）

---

## 文件 3：`services/decision/src/llm/prompts.py`

Prompt 模板管理。

```python
RESEARCHER_SYSTEM = """你是一个专业的量化策略研究员。
根据用户的策略意图描述，生成完整的 Python 策略代码。
代码必须包含：信号生成函数、参数定义、回测入口。
只输出代码，不要解释。"""

AUDITOR_SYSTEM = """你是一个严格的策略审核员。
审核以下策略代码的：
1. 逻辑正确性（信号是否合理）
2. 风险参数（止损/止盈是否设置）
3. 过拟合风险（参数数量是否过多）
4. 代码质量（是否有明显 bug）
输出 JSON 格式：{"passed": bool, "issues": [...], "risk_level": "low|medium|high", "summary": "..."}"""

ANALYST_SYSTEM = """你是一个数据分析师。
根据以下策略绩效数据，分析：
1. 收益来源归因
2. 最大回撤发生原因
3. 改进建议（参数调整方向）
输出结构化分析报告。"""
```

---

## 文件 4：`services/decision/src/llm/pipeline.py`

三模型串行流水线核心。

```python
class LLMPipeline:
    def __init__(self, client: OllamaClient):
        self.client = client
        self.researcher_model = os.getenv("OLLAMA_RESEARCHER_MODEL", "deepcoder:14b")
        self.auditor_model = os.getenv("OLLAMA_AUDITOR_MODEL", "qwen3:14b")
        self.analyst_model = os.getenv("OLLAMA_ANALYST_MODEL", "phi4-reasoning:14b")

    async def research(self, intent: str) -> dict:
        """调用 deepcoder 生成策略代码"""

    async def audit(self, code: str) -> dict:
        """调用 qwen3 审核策略代码"""

    async def analyze(self, performance_data: dict) -> dict:
        """调用 phi4-reasoning 分析绩效"""

    async def full_pipeline(self, intent: str) -> dict:
        """
        完整流水线：research → audit → analyze
        串行执行，每步等上一步完成。
        返回 {
            "research_result": {...},
            "audit_result": {...},
            "analysis_result": {...},
            "total_duration_seconds": float
        }
        """
```

要求：
- 串行执行，不并发
- 每步记录耗时
- 任一步骤失败→返回已完成步骤的结果 + error 字段，不继续后续步骤
- full_pipeline 中 analyze 步骤：如果 audit 结果 passed=false，跳过 analyze 直接返回

---

## 文件 5：`services/decision/src/api/routes/llm.py`

API 路由，暴露 4 个端点。

```python
router = APIRouter(prefix="/api/v1/llm", tags=["llm"])

@router.post("/research")     # 单独调用策略研究
@router.post("/audit")        # 单独调用策略审核
@router.post("/analyze")      # 单独调用绩效分析
@router.post("/pipeline")     # 完整流水线（串行三步）
```

请求/响应模型使用 Pydantic BaseModel。

---

## 文件 6：`services/decision/tests/test_llm_pipeline.py`

至少 6 个测试用例：
1. OllamaClient 超时处理（mock httpx 超时）
2. OllamaClient 正常返回解析
3. LLMPipeline.research 正常调用
4. LLMPipeline.audit 正常调用
5. LLMPipeline.full_pipeline 审核不通过时跳过 analyze
6. LLMPipeline.full_pipeline 正常串行完成

使用 `unittest.mock.AsyncMock` mock OllamaClient.chat，不要真正调用 Ollama。

---

## 文件 7：`services/decision/src/api/app.py`（修改）

在现有路由注册末尾添加 LLM 路由。

**当前末尾是：**
```python
    app.include_router(local_sim_router, prefix="/api/v1/stock")

    return app
```

**改为：**
```python
    app.include_router(local_sim_router, prefix="/api/v1/stock")
    # CF1' LLM Pipeline
    from .routes.llm import router as llm_router
    app.include_router(llm_router)

    return app
```

---

## 编码约束

1. **Python 3.9 兼容**：用 `Optional[str]` 不要用 `str | None`，用 `list[dict]` 不要用 `dict | None`
2. 不要修改白名单以外的文件
3. 不要添加新的 pip 依赖（httpx 已存在）
4. API Key 认证已在 `app.py` 全局中间件处理，路由不需要认证逻辑
5. 日志用 `logging.getLogger(__name__)`

## commit 格式

```
feat(decision): TASK-0081 CF1' LLM三模型串行流水线
```

## 完成后汇报

1. commit hash
2. 测试运行结果
3. 任何遇到的问题
