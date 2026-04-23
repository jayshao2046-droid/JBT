# TASK-U0-20260423-decision-llm-flow-fix

**任务类型**: U0 极速维修  
**创建时间**: 2026-04-23  
**服务范围**: decision (单服务)  
**优先级**: P0  
**状态**: 进行中

---

## 一、任务背景

Atlas 完成 Studio Decision LLM 自动化流程只读检查，发现 2 个 P0 问题和 2 个 P1 问题需要修复。

**诊断报告**: `/tmp/decision_llm_flow_check.md`

---

## 二、问题清单

### P0 问题（必须修复）

| # | 问题 | 影响 | 位置 |
|---|------|------|------|
| 1 | **TTL 缓存时差风险** | Mini 预读 21:00 生成，Decision 08:30 消费，8小时 TTL 可能导致缓存失效 | `src/llm/context_loader.py:23` |
| 2 | **研报端点 404 静默失败** | L2 审查时研报缺失仅记录 INFO，未触发 P1 告警 | `src/llm/context_loader.py:323-326` |

### P1 问题（建议修复）

| # | 问题 | 影响 | 位置 |
|---|------|------|------|
| 3 | **tqsdk 配置缺失无告警** | 环境变量未配置时静默跳过，无明确提示 | `src/llm/pipeline.py:593-597` |
| 4 | **研究员报告去重窗口固定** | 15分钟去重窗口硬编码，无法根据报告频率动态调整 | `src/api/routes/researcher_evaluate.py:22` |

### P2 问题（优化修复）

| # | 问题 | 影响 | 位置 |
|---|------|------|------|
| 5 | **ResearchStore 无时间维度清理** | 当前只保留最近 50 条，无过期时间清理，长期运行可能积累过期数据 | `src/research/research_store.py:63-66` |

---

## 三、修复方案

### 修复 1: TTL 缓存时差（P0）

**文件**: `services/decision/src/llm/context_loader.py`

**修改**:
```python
# 第 23 行
# 原: TTL_SECONDS = 8 * 3600  # 8 小时缓存
# 改为:
TTL_SECONDS = 12 * 3600  # 12 小时缓存（覆盖 21:00 → 08:30 时差）
```

**理由**: Mini 预读在 21:00 生成，Decision 在次日 08:30 消费，时差 11.5 小时，8 小时 TTL 会导致缓存失效。

---

### 修复 2: 研报 404 告警（P0）

**文件**: `services/decision/src/llm/context_loader.py`

**修改**: 在 `get_l2_context()` 函数中，研报 404 时触发 P1 告警

```python
# 第 323-326 行附近
except httpx.HTTPStatusError as exc:
    if exc.response.status_code == 404:
        logger.info(f"L2 上下文：研报 API 未就绪 (404)，TASK-0110 可能未部署")
        missing_sources.append("研报摘要")
        context_parts.append("\n[DATA_DEGRADED] 研报摘要缺失（API 未就绪）")
        # 新增：触发 P1 告警（研报缺失属于数据降级，需要告警）
        # 注意：此处无法直接调用 _send_data_missing_alert（它是 GateReviewer 的方法）
        # 改为记录 WARNING 日志，由调用方（GateReviewer）统一处理
```

**实际方案**: 由于 `get_l2_context()` 是独立函数，无法直接调用 `GateReviewer._send_data_missing_alert()`，改为：
1. 将 404 日志级别从 INFO 提升为 WARNING
2. 在 `GateReviewer.l2_deep_review()` 中，检查 `missing_sources` 是否包含"研报摘要"，如果包含则触发告警

---

### 修复 3: tqsdk 配置检查（P1）

**文件**: `services/decision/src/llm/pipeline.py`

**修改**: 在 `_sync_fetch_tqsdk()` 函数开头增加配置检查

```python
# 第 626 行附近
@staticmethod
def _sync_fetch_tqsdk(symbol: str, duration_seconds: int, username: str, password: str) -> list:
    """同步 tqsdk 拉取（在 executor 中运行）。"""
    api = None
    try:
        # 新增：配置检查
        if not username or not password:
            logger.warning("[KLINE] tqsdk 账号未配置（TQSDK_AUTH_USERNAME/PASSWORD），跳过实时 K 线拉取")
            return []
        
        from tqsdk import TqApi, TqAuth
        # ... 原有逻辑
```

---

### 修复 4: 去重窗口可配置（P1）

**文件**: `services/decision/src/api/routes/researcher_evaluate.py`

**修改**: 将硬编码的 900 秒改为从环境变量读取（已经实现，但需要在 `.env.example` 中补充说明）

```python
# 第 22 行（已实现，无需修改代码）
_DEDUP_SECONDS = int(os.getenv("RESEARCHER_SCORE_DEDUP_SECONDS", "900"))
```

**补充**: 在 `.env.example` 中增加说明：
```bash
# ----- 研究员报告评级配置 -----
RESEARCHER_SCORE_DEDUP_SECONDS=900
# 研究员报告去重窗口（秒），同 report_type+report_id 在窗口内只处理一次
```

---

### 修复 5: ResearchStore 时间维度清理（P2）

**文件**: `services/decision/src/research/research_store.py`

**修改**: 在 `save()` 方法中增加时间维度清理逻辑

```python
# 第 59-66 行附近
def save(self, report_type: str, record: dict[str, Any]) -> None:
    """保存一条评级结果"""
    record.setdefault("stored_at", datetime.now().isoformat())
    self._cache[report_type].append(record)
    
    # 保留最近 N 条
    if len(self._cache[report_type]) > _MAX_HISTORY:
        self._cache[report_type] = self._cache[report_type][-_MAX_HISTORY:]
    
    # 新增：时间维度清理（保留最近 7 天）
    max_age_days = int(os.getenv("RESEARCH_STORE_MAX_AGE_DAYS", "7"))
    cutoff = datetime.now() - timedelta(days=max_age_days)
    self._cache[report_type] = [
        r for r in self._cache[report_type]
        if datetime.fromisoformat(r.get("stored_at", "1970-01-01")) > cutoff
    ]
    
    self._persist(report_type)
    logger.info("ResearchStore: 保存 %s (score=%.1f)", report_type, record.get("score", 0))
```

**需要导入**: 在文件顶部增加 `import os` 和 `from datetime import timedelta`

**补充**: 在 `.env.example` 中增加说明：
```bash
# ----- 研报存储配置 -----
RESEARCH_STORE_MAX_AGE_DAYS=7
# 研报评级结果保留天数，超过此时间的记录将被自动清理
```

---

## 四、修复文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `services/decision/src/llm/context_loader.py` | 修改 | TTL 8h → 12h + 研报 404 日志级别提升 |
| `services/decision/src/llm/gate_reviewer.py` | 修改 | L2 深审中检查研报缺失并触发告警 |
| `services/decision/src/llm/pipeline.py` | 修改 | tqsdk 配置检查增强 |
| `services/decision/src/research/research_store.py` | 修改 | 增加时间维度清理（7天过期） |
| `services/decision/.env.example` | 修改 | 补充配置说明（去重窗口 + 存储过期时间） |

---

## 五、验收标准

### 修复 1 验收
- [ ] `context_loader.py` 中 `TTL_SECONDS = 12 * 3600`
- [ ] 注释说明时差覆盖逻辑

### 修复 2 验收
- [ ] 研报 404 日志级别为 WARNING
- [ ] `GateReviewer.l2_deep_review()` 中研报缺失触发 P1 告警

### 修复 3 验收
- [ ] tqsdk 账号未配置时记录 WARNING 日志
- [ ] 日志明确提示环境变量名称

### 修复 4 验收
- [ ] `.env.example` 中补充 `RESEARCHER_SCORE_DEDUP_SECONDS` 说明

### 修复 5 验收
- [ ] `research_store.py` 中增加时间维度清理逻辑
- [ ] 导入 `os` 和 `timedelta`
- [ ] `.env.example` 中补充 `RESEARCH_STORE_MAX_AGE_DAYS` 说明

### 整体验收
- [ ] 所有文件 `python3 -m py_compile` 语法检查通过
- [ ] 修改后 Studio Decision 容器重启成功
- [ ] `/health` 端点返回 ok

---

## 六、U0 约束遵守

- ✅ 单服务修复：仅涉及 decision 服务
- ✅ 最小改动：5 个文件，预计 < 30 行代码修改
- ✅ 无跨服务依赖：不涉及 data/sim-trading/backtest 服务
- ✅ 可独立验证：修改后可立即重启容器验证

---

## 七、风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| TTL 调整导致内存占用增加 | 低 | 缓存对象很小（< 1MB），12h vs 8h 影响可忽略 |
| 研报告警频繁触发 | 低 | 仅在研报 API 未就绪时触发，正常运行不会告警 |
| tqsdk 日志噪音 | 低 | 仅在未配置时记录一次 WARNING |

---

**创建人**: Atlas  
**执行人**: Atlas (U0 模式)  
**预计耗时**: 15 分钟  
**状态**: 待执行
