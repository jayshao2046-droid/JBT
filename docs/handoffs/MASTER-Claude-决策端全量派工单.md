# MASTER Claude 派工单 — 决策端全量实装（7 批次一次性执行）

【派工时间】2026-04-15  
【复核人】Atlas（统一验收）  
【执行 Agent】Claude-Code（决策 Agent 身份）  
【执行模式】**顺序执行 Batch A→B→C，C 完成后 0114/0115/0116/0117 可并行**

---

## 概览

本派工单涵盖决策端当前所有待实装任务，包含：

| 任务 | 名称 | Token | 依赖 |
|------|------|-------|------|
| TASK-0112 Batch A | 口径修正 + phi4 L1/L2 门控实装 | `tok-0a2faa03-6f93-4300-bb31-756af285b6bc` | 无 |
| TASK-0112 Batch B | deepcoder 夜间策略调优 + 沙箱回测接入 | `tok-08de1aff-99ac-44f3-af40-3f2899ccf1b7` | Batch A |
| TASK-0112 Batch C | Optuna 调度 + full_pipeline() 串联 | `tok-370db4de-07c8-4adb-a591-ea8cdc730bbb` | Batch B |
| TASK-0114 | 35 品种自适应模型注册表 | `tok-d0112f40-fa4d-4368-9f4b-12e20952d6e7` | Batch C |
| TASK-0115 | 信号失真检测 + 因子漂移监控（G8）| `tok-48fd42a7-96d5-441e-8da2-2b047a49cbaa` | 独立（Batch C 后并行）|
| TASK-0116 | 因子挖掘自动化 | `tok-bc3f9282-fb3e-4c90-8484-680d6be0e752` | 独立（Batch C 后并行）|
| TASK-0117 | 研究中心 5 项拓展 | `tok-f8d27abe-32ad-4b21-beae-fe03e6596ba7` | Batch C |

---

## 开工前必读（全局）

1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/决策提示词.md`
4. `docs/tasks/TASK-0112-decision-模型口径修正与三级门控实装.md`

---

## 架构事实（Jay.S 确认，2026-04-15）

### Ollama 模型分布

| 主机 | IP | 模型 | 角色 |
|------|----|------|------|
| Studio | 192.168.31.142 | phi4-reasoning:14b | L1/L2 门控审稿（盘中）|
| Studio | 192.168.31.142 | deepcoder:14b | 策略调优 + 因子挖掘（夜间）|
| Studio | 192.168.31.142 | qwen3:14b | 备用 |
| Alienware | 192.168.31.223 | qwen3:14b | 数据研究员（TASK-0110）|

### DashScope 在线模型

| 模型 | 角色 |
|------|------|
| Qwen3.6-Plus | 默认在线确认（L3）|
| Qwen3-Max | 升级复核 |
| DeepSeek-V3.2 | 在线备援 |
| DeepSeek-R1 | 争议复核 |

### 数据源硬规则

**phi4 和 deepcoder 只允许读取两类数据源：**
1. 研报：`GET {DATA_API_URL}/api/v1/researcher/report/latest`
2. K 线：`GET {DATA_API_URL}/api/v1/bars` / `GET {DATA_API_URL}/api/v1/stocks/bars`

**数据缺失报警规则**：研报为空或 K 线缺失 → 飞书 P1 (orange ⚠️) + 降级继续（不 hold）

### K 线窗口
- L1：5 日日线
- L2：20 日日线 + 60 根分钟线 + 研报摘要

### 不存在的模型（必须从代码中清除）
- ❌ Qwen2.5（signal.py L1 profile 错误引用）
- ❌ DeepSeek-R1-14B（.env 配置值，未安装）
- ❌ qwen3:14b 作为 pipeline auditor

---

## STEP 1：TASK-0112 Batch A（必须先执行）

**Token**: `tok-0a2faa03-6f93-4300-bb31-756af285b6bc`  
**详细规格**: `docs/handoffs/TASK-0112-Claude-决策端门控实装派工单.md` → Batch A 章节

**白名单**:
- `services/decision/src/api/routes/signal.py`
- `services/decision/src/llm/pipeline.py`
- `services/decision/src/llm/gate_reviewer.py`（新建）
- `services/decision/src/llm/context_loader.py`
- `services/decision/tests/test_signal_gate.py`（新建）

**完工验收**：`pytest services/decision/tests/test_signal_gate.py -v` 全通过后继续 Batch B。

---

## STEP 2：TASK-0112 Batch B（Batch A 完成后）

**Token**: `tok-08de1aff-99ac-44f3-af40-3f2899ccf1b7`  
**详细规格**: `docs/handoffs/TASK-0112-Claude-决策端门控实装派工单.md` → Batch B 章节

**白名单**:
- `services/decision/src/research/evening_rotation.py`
- `services/decision/src/research/optuna_search.py`
- `services/decision/src/research/sandbox_runner.py`（新建）
- `services/decision/tests/test_evening_rotation.py`（新建）

**完工验收**：`pytest services/decision/tests/test_evening_rotation.py -v` 全通过后继续 Batch C。

---

## STEP 3：TASK-0112 Batch C（Batch B 完成后）

**Token**: `tok-370db4de-07c8-4adb-a591-ea8cdc730bbb`  
**详细规格**: `docs/handoffs/TASK-0112-Claude-决策端门控实装派工单.md` → Batch C 章节

**白名单**:
- `services/decision/src/llm/pipeline.py`（修改：full_pipeline()）
- `services/decision/src/research/evening_rotation.py`（修改：rotate() 接 _score_stock()）
- `services/decision/src/research/optuna_search.py`（修改：schedule_nightly()）
- `services/decision/src/research/trainer.py`（修改：真实 Sharpe）
- `services/decision/tests/test_research_pipeline.py`（新建）

**完工验收**：`pytest services/decision/tests/test_research_pipeline.py -v` 全通过后可并行执行 STEP 4-7。

---

## STEP 4：TASK-0114（Batch C 完成后，可与 0115/0116/0117 并行）

**Token**: `tok-d0112f40-fa4d-4368-9f4b-12e20952d6e7`  
**详细规格**: `docs/handoffs/TASK-0114-Claude-品种级自适应模型注册表派工单.md`

**白名单**:
- `services/decision/src/research/model_registry.py`（新建）
- `services/decision/src/research/regime_detector.py`（新建）
- `services/decision/src/research/trainer.py`（修改，以 Batch C 为基础继续扩展）
- `services/decision/tests/test_model_registry.py`（新建）

**完工验收**：`pytest services/decision/tests/test_model_registry.py -v` 全通过。

---

## STEP 5：TASK-0115（Batch C 完成后，可并行）

**Token**: `tok-48fd42a7-96d5-441e-8da2-2b047a49cbaa`  
**详细规格**: `docs/handoffs/TASK-0115-Claude-信号失真检测派工单.md`

**白名单**:
- `services/decision/src/research/signal_validator.py`（新建）
- `services/decision/src/research/factor_monitor.py`（新建）
- `services/decision/tests/test_signal_validator.py`（新建）

**完工验收**：`pytest services/decision/tests/test_signal_validator.py -v` 全通过。

---

## STEP 6：TASK-0116（Batch C 完成后，可并行）

**Token**: `tok-bc3f9282-fb3e-4c90-8484-680d6be0e752`  
**详细规格**: `docs/handoffs/TASK-0116-Claude-因子挖掘自动化派工单.md`

**白名单**:
- `services/decision/src/research/factor_miner.py`（新建）
- `services/decision/src/research/factor_validator.py`（新建）
- `services/decision/src/api/routes/factor.py`（新建）
- `services/decision/tests/test_factor_mining.py`（新建）

**完工验收**：`pytest services/decision/tests/test_factor_mining.py -v` 全通过。

---

## STEP 7：TASK-0117（Batch C 完成后，可并行）

**Token**: `tok-f8d27abe-32ad-4b21-beae-fe03e6596ba7`  
**详细规格**: `docs/handoffs/TASK-0117-Claude-研究中心五项拓展派工单.md`

**白名单**:
- `services/decision/src/research/spread_monitor.py`（新建）
- `services/decision/src/research/news_scorer.py`（新建）
- `services/decision/src/research/correlation_monitor.py`（新建）
- `services/decision/src/reporting/daily.py`（修改）
- `services/decision/src/api/routes/optimizer.py`（修改）
- `services/decision/tests/test_research_extensions.py`（新建）

**完工验收**：`pytest services/decision/tests/test_research_extensions.py -v` 全通过。

---

## 全量完工后操作

所有 7 步完成后：

### 1. 综合测试
```bash
cd /Users/jayshao/JBT
pytest services/decision/tests/ -v --tb=short 2>&1 | tail -50
```

### 2. 向 Atlas 汇报结果
汇报内容含：
- 每个 Batch 的测试结果（通过/失败数）
- 任何 get_errors() 发现的问题
- 新增文件清单

### 3. Atlas 统一验收后操作
- Atlas 确认通过 → 重启 Studio decision 容器（生产上线）
- 重启命令（由 Atlas/Jay.S 执行）：`ssh jayshao@192.168.31.142 "cd ~/JBT && docker compose restart decision"`

### 4. 禁止事项
- **不得**在 Atlas 确认前执行 git commit
- **不得**独立修改白名单外任何文件
- **不得**直接部署到生产环境

---

## 依赖检验清单

执行前确认以下已完成：
- [ ] TASK-0110（数据研究员 qwen3）已部署并运行（researcher/report/latest 可访问）
- [ ] TASK-0112 Batch A Token 有效（`tok-0a2faa03`）
- [ ] TASK-0112 Batch B Token 有效（`tok-08de1aff`）
- [ ] TASK-0112 Batch C Token 有效（`tok-370db4de`）
- [ ] TASK-0114 Token 有效（`tok-d0112f40`）
- [ ] TASK-0115 Token 有效（`tok-48fd42a7`）
- [ ] TASK-0116 Token 有效（`tok-bc3f9282`）
- [ ] TASK-0117 Token 有效（`tok-f8d27abe`）
