# TASK-0112 — 决策端模型口径修正与三级门控实装

【创建】2026-04-15
【服务归属】`services/decision/`
【执行 Agent】Claude-Code
【复核】Atlas
【状态】建档完成，待签发

## 任务概述

修正决策端代码中 6 处模型名与实际部署不符的错误口径，并实装 phi4-reasoning:14b 的 L1/L2 真实 LLM 门控（当前为纯规则引擎贴标签），以及 L3 在线模型（DashScope）的条件触发确认。

## 背景

2026-04-15 Jay.S 确认的修正后架构：
- Studio: deepcoder:14b（策略调优）+ phi4-reasoning:14b（L1/L2 盘中门控）+ qwen3:14b（备用）
- Alienware: qwen3:14b（数据研究员，归属 data 服务）
- L3 在线: Qwen3.6-Plus / Qwen3-Max / DeepSeek-V3.2 / DeepSeek-R1（DashScope API）
- phi4 决策依据：Alienware qwen3 研报 + 5日K线
- ❌ 不存在 Qwen2.5；❌ DeepSeek-R1-14B 未安装

## 分批计划

### Batch A — 口径修正 + phi4 L1/L2 门控实装（P1，5 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/api/routes/signal.py` | 修改 | L1/L2 profile 从 Qwen2.5/Qwen3 改为 phi4-reasoning:14b；review 路径接入真实 LLM 调用 |
| `services/decision/src/llm/pipeline.py` | 修改 | auditor_model 默认从 qwen3:14b 改为 phi4-reasoning:14b |
| `services/decision/src/llm/gate_reviewer.py` | 新建 | phi4 L1 快审 + L2 深审封装：读研报 + 5日K线，输出 JSON {pass, risk_flag, confidence, reasoning} |
| `services/decision/src/llm/context_loader.py` | 修改 | 扩展：拉取 Alienware qwen3 研报 + data API 5日K线注入 gate context |
| `services/decision/tests/test_signal_gate.py` | 新建 | phi4 门控测试：mock Ollama 验证 L1 拒绝/L2 通过路径 |

### Batch B — L3 在线模型接入（P1，4 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/llm/online_confirmer.py` | 新建 | DashScope OpenAI-compatible API 封装；默认 Qwen3.6-Plus，争议走 DeepSeek-R1；失败降级为 L2 结论 |
| `services/decision/src/api/routes/signal.py` | 修改 | L2 approve 后按触发条件（signal_strength>阈值/L1 L2 评分不一致）调 L3 |
| `services/decision/src/api/routes/model.py` | 修改 | online_models 从硬编码空改为读取 .env 配置 |
| `services/decision/tests/test_online_confirmer.py` | 新建 | L3 在线模型测试：mock DashScope 验证正常/降级路径 |

## 质量标准

- L1 审查延迟 < 5s（phi4 快速门审）
- L2 审查延迟 < 15s（phi4 深度审查）
- L3 延迟 < 30s，DashScope 失败自动降级为 L2 结论
- JSON 输出可解析率 > 95%
- 全部测试通过

## 依赖

- Batch B 依赖 Batch A（signal.py 先完成 L1/L2 才能接 L3）
- TASK-0110 数据研究员 API 完成前，context_loader 先用 data API 直接读取
