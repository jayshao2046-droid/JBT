# TASK-0021 C 批 — 决策服务核心骨架 交接单

【任务】TASK-0021 C 批  
【执行 Agent】决策 Agent  
【Token】tok-763ac85c-81a5-46f2-b04b-0f66035dedc5  
【Review ID】REVIEW-TASK-0021-C  
【完成时间】2026-04-07  
【状态】待项目架构师终审 → lockback

---

## 一、文件清单（23 个，全部 0 errors）

### 项目配置层
| 文件 | 说明 |
|---|---|
| `services/decision/pyproject.toml` | Poetry 项目配置，依赖 fastapi/uvicorn/pydantic-settings/httpx |

### 入口层
| 文件 | 说明 |
|---|---|
| `services/decision/src/__init__.py` | 包标识 |
| `services/decision/src/main.py` | uvicorn 启动入口，读取 Settings，支持 development reload |

### core 层
| 文件 | 说明 |
|---|---|
| `services/decision/src/core/__init__.py` | 包标识 |
| `services/decision/src/core/settings.py` | pydantic-settings，读取 .env.example 所有字段（host/port/env/gate/model-router/urls 等） |

### API 层
| 文件 | 说明 |
|---|---|
| `services/decision/src/api/__init__.py` | 包标识 |
| `services/decision/src/api/app.py` | FastAPI 实例，include 5 个 router |
| `services/decision/src/api/routes/__init__.py` | 包标识 |
| `services/decision/src/api/routes/health.py` | GET /health + GET /ready |
| `services/decision/src/api/routes/strategy.py` | GET/POST /strategies, GET /strategies/{id}, GET /strategies/{id}/lifecycle |
| `services/decision/src/api/routes/signal.py` | POST /signals/review + GET /signals/{decision_id} |
| `services/decision/src/api/routes/approval.py` | POST /approvals/submit, GET /approvals/{id}, POST /approvals/{id}/complete |
| `services/decision/src/api/routes/model.py` | GET /models/status + POST /models/route |

### strategy 层
| 文件 | 说明 |
|---|---|
| `services/decision/src/strategy/__init__.py` | 包标识 |
| `services/decision/src/strategy/lifecycle.py` | 8 状态机（imported→reserved→researching→research_complete→backtest_confirmed→pending_execution→in_production→archived），非法转换抛 ValueError |
| `services/decision/src/strategy/repository.py` | 内存字典，create/get/list/update/delete/transition_lifecycle/list_by_status |

### model 层
| 文件 | 说明 |
|---|---|
| `services/decision/src/model/__init__.py` | 包标识 |
| `services/decision/src/model/router.py` | 回测证明 + 研究快照双门禁，返回 `{"allowed": bool, "reason": str}` |

### gating 层
| 文件 | 说明 |
|---|---|
| `services/decision/src/gating/__init__.py` | 包标识 |
| `services/decision/src/gating/execution_gate.py` | sim-trading 开放；live-trading 若 `LIVE_TRADING_GATE_LOCKED=true` 则返回 eligible=false |

### 测试层
| 文件 | 说明 |
|---|---|
| `services/decision/tests/__init__.py` | 包标识 |
| `services/decision/tests/test_health.py` | test_health_ok / test_ready_ok，httpx AsyncClient |
| `services/decision/tests/test_strategy.py` | test_create_strategy / test_get_nonexistent_strategy / test_lifecycle_transition_valid / test_lifecycle_transition_invalid |

---

## 二、API 端点列表

| 方法 | 路径 | 功能 |
|---|---|---|
| GET | /health | 服务健康 |
| GET | /ready | 就绪探针 |
| GET | /strategies | 列出所有策略 |
| POST | /strategies | 创建策略包 |
| GET | /strategies/{id} | 获取单策略 |
| GET | /strategies/{id}/lifecycle | 获取生命周期状态 |
| POST | /signals/review | 提交信号审查（返回 DecisionResult 骨架） |
| GET | /signals/{decision_id} | 获取决策结果 |
| POST | /approvals/submit | 提交审批请求 |
| GET | /approvals/{id} | 查询审批状态 |
| POST | /approvals/{id}/complete | 完成审批（approve/reject） |
| GET | /models/status | 当前门禁配置状态 |
| POST | /models/route | 触发模型路由门禁检查 |

---

## 三、测试结果

```
6 passed in 0.33s
test_health_ok          PASSED
test_ready_ok           PASSED
test_create_strategy    PASSED
test_get_nonexistent_strategy  PASSED
test_lifecycle_transition_valid   PASSED
test_lifecycle_transition_invalid PASSED
```

---

## 四、质量核验

- [x] 全部 23 文件 0 errors（get_errors 确认）
- [x] 无跨服务 import（未引用 backtest/sim-trading/data/live-trading 任何代码）
- [x] pydantic v2 syntax（使用 `model_config = SettingsConfigDict(...)` 而非 v1 `orm_mode`）
- [x] 端口 8104（对齐 .env.example）
- [x] live-trading gate locked（对齐契约和 .env.example）

---

## 五、架构师终审要点

1. `lifecycle.py` 使用 8 状态内部状态机，而契约 `strategy_package.md` 定义 5 状态外部模型，两者并存，内部状态机更细粒度，`repository.to_dict()` 直接暴露内部 8 状态；**如需对外收口为契约 5 状态，请在终审中指示。**
2. `signal.py` 中 `POST /signals/review` 返回骨架（action=hold, confidence=0），实际 LLM/XGBoost 推理引擎未接入，此为 C 批边界。
3. 策略仓库为纯内存（无持久化），重启后清空；数据库层在后续批次接入。
