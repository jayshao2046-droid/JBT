# REVIEW-P1-20260424F3 — Decision macro 评分识别 source_report.data_coverage

**审核日期**：2026-04-24  
**审核人**：项目架构师  
**任务单**：docs/tasks/TASK-P1-20260424F3-Decision-macro评分修正.md  
**审核状态**：✅ 预审通过

---

## 一、服务归属确认

| 检查项 | 结论 |
|--------|------|
| 服务归属 | ✅ `services/decision` — researcher qwen3 scorer，归属正确 |
| 执行设备 | ✅ MacBook 改代码 → rsync 同步 Studio → docker restart JBT-DECISION-8104 |
| 影响范围 | ✅ 仅 Studio decision 服务，不涉及 Alienware / Mini / Air |

---

## 二、白名单确认

**申报白名单（1 文件）**：
- `services/decision/src/llm/researcher_qwen3_scorer.py`

**架构师核验**：
- ✅ `research_store.py` 不需要加入（只改字段提取，不改存储结构）
- ✅ `research_query.py` 不需要加入（API 响应字段类型不变）
- ✅ `shared/contracts` 不需要变更（`observed_content` 是已有 string 字段，内容丰富化不是 schema 变更）

**白名单确认：1 文件，与申报一致，无遗漏。**

---

## 三、改动合规性分析

### 3.1 服务隔离

| 边界 | 结论 |
|------|------|
| 不跨服务 import | ✅ 改动仅读取传入的 `report` 参数 dict，无新 import |
| 不读写 data 服务运行时目录 | ✅ |
| 不改 `shared/contracts` | ✅ |
| 不改 Mini 文件（永久禁区） | ✅ |

### 3.2 _normalize_report 返回结构确认

返回 dict key 集合不变（只追加 `observed_parts` 内容，join 逻辑不变）：
- ✅ `_score_report_full` 中的 macro 评分规则分支不受影响
- ✅ 其他调用 `_normalize_report` 的路径返回结构完全兼容

### 3.3 插入点合规性确认

插入点：`observed_parts` 列表构建之后、`return {}` 之前。  
`report_type`、`observed_parts`、`report` 均已在 scope 内，插入合法。

### 3.4 防御性编码核验

| 字段路径 | 防护 | 结论 |
|---------|------|------|
| `report.get("source_report") or {}` | ✅ 空值 fallback | 安全 |
| `source_report.get("data_coverage") or {}` | ✅ 空值 fallback | 安全 |
| `if data_coverage:` 守卫 | ✅ 跳过空 coverage | 安全 |
| `[... if v]` 过滤零值 | ✅ | 安全 |
| `key_drivers[:3]` 截断 | ✅ 防 observed_content 过长 | 安全 |

### 3.5 其他报告类型不受影响

改动全部在 `if report_type == "macro":` 分支内，news / futures / stocks 评分不变。

---

## 四、F2 × F3 并行安全确认

✅ 无文件交集，无服务交集，可完全并行执行。

---

## 五、预审结论

**结论：✅ 预审通过，无附加条件**

改动约 15 行，只加不减，防御性编码到位，验收标准明确，风险极低。

**待签发 Token**：
- `services/decision/src/llm/researcher_qwen3_scorer.py`（1 文件）
