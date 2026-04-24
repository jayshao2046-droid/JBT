# REVIEW-P1-20260424F2 — stream cycle 接回 daily_stats 埋点

**审核日期**：2026-04-24  
**审核人**：项目架构师  
**任务单**：docs/tasks/TASK-P1-20260424F2-stream-cycle接回daily-stats.md  
**审核状态**：⚠️ 条件通过（实施前须修正 record_report 调用签名）

---

## 一、服务归属确认

| 检查项 | 结论 |
|--------|------|
| 服务归属 | ✅ `services/data` — researcher scheduler，归属正确 |
| 执行设备 | ✅ MacBook 改代码 → rsync 同步 Alienware → 重启裸 Python researcher 进程 |
| 影响范围 | ✅ 仅 Alienware sim-trading 节点，不涉及 Mini / Studio / Air |

---

## 二、白名单确认

**申报白名单（1 文件）**：
- `services/data/src/researcher/scheduler.py`

**架构师核验结论**：
- ✅ 白名单范围正确，改动仅在 `execute_stream_cycle` 函数尾部新增 try/except 埋点
- ✅ `daily_stats.py` 不需要进入白名单（`record_report` 接口已有，不改实现）
- ✅ 明确排除列表完整，无遗漏依赖文件需加入白名单

**白名单确认：1 文件，与申报一致。**

---

## 三、改动合规性分析

### 3.1 服务隔离

| 边界 | 结论 |
|------|------|
| 不跨服务 import | ✅ 仅调用 `self.reporter.stats_tracker.record_report()`，链路全在 `services/data` 内 |
| 不读写其他服务运行时目录 | ✅ |
| 不改 `shared/contracts` | ✅ |
| 不改 Mini 文件（永久禁区） | ✅ |

### 3.2 变量可达性核验

插入点：`execute_stream_cycle` 函数尾部，`elapsed = time.time() - start_time` 之后、`return {...}` 之前。

| 变量 | 可达性 |
|------|--------|
| `now` | ✅ L1128 `now = datetime.now()` |
| `today` | ✅ L1135 `today = now.strftime(...)` |
| `elapsed` | ✅ 插入点上方已计算 |
| `errors` | ✅ L1130 `errors = []` |
| `analyzed` | ✅ 在同函数日志行中引用，在 scope 内 |
| `self.reporter.stats_tracker` | ✅ 已在 L56 / L82 / L219 / L241 中稳定使用 |

### 3.3 ⚠️ 关键修正项：record_report 接口不支持 content_bytes

**问题描述**：  
任务单中拟传入 `content_bytes=content_bytes` 参数，但 `daily_stats.py::record_report()` 的实际签名为：

```python
def record_report(self, hour: int, report_id: str, json_path: str, elapsed_s: float, success: bool)
```

该方法**不接受** `content_bytes` 参数。若照原样实现，将在 try 块内触发 `TypeError`，被 except 静默捕获，导致统计埋点完全无效（`reports_generated` 永远不递增）。

**修正要求**：实施时必须使用以下签名：

```python
self.reporter.stats_tracker.record_report(
    hour=now.hour,
    report_id=report_id_for_stats,
    json_path="",
    elapsed_s=elapsed,
    success=(len(errors) == 0),
)
```

**此修正为实施前强制前提，不得遗漏。**

### 3.4 主链无副作用确认

- ✅ try/except 包裹，任何写入异常不阻断主链 return
- ✅ `report_id` 前缀 `STREAM-` 与 `execute_hourly` 的 `RPT-` 不冲突
- ✅ `success=(len(errors) == 0)` 语义正确

---

## 四、F1 串行约束确认

**约束指定**：F2 先锁回 → F1 实施时必须以 F2 合并后代码为基线，完整 rebase。  
F1 实施 Agent 在拿到 Token 后，必须先确认 F2 已完成 Lockback，再开始改动 `scheduler.py`。

---

## 五、F2 × F3 并行安全确认

✅ 无文件交集（F2: scheduler.py，F3: researcher_qwen3_scorer.py），可完全并行。

---

## 六、预审结论

**结论：⚠️ 条件通过**

**放行条件（实施前必须满足）**：
1. ✅ 移除 `record_report()` 调用中的 `content_bytes` 参数（强制）
2. ✅ 确认 F1 尚未对 scheduler.py 提交任何变更，F2 基于当前 HEAD 实施

**待签发 Token**：
- `services/data/src/researcher/scheduler.py`（1 文件）
