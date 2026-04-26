# TASK-P1-20260425G1 — decision 侧 qwen3 策略研发链路独立训练

## 任务类型
- P1 标准流程
- 服务归属：services/decision
- 协同设备：Studio（训练 + 部署验证）
- 当前状态：仅建档，待项目架构师预审；未冻结文件白名单，未申请 Token
- 启动口径（2026-04-25 收紧）：本任务作为 Studio 14B 后继任务，必须在 researcher 14B 与 researcher 7B 两条训练线均完成后再启动实施
- 明确边界：本任务独立于当前 researcher F4/F5 LoRA 训练，不复用 data 侧 adapter 直接上线 decision

## 背景与根因
2026-04-25 Atlas 只读核对确认：decision 侧的 qwen3:14b-q4_K_M 已不只是研究员评分器，而是同时承担 4 类策略研发职责：

1. `services/decision/src/llm/pipeline.py` 中 `research()`：按策略意图生成策略代码。
2. `services/decision/src/llm/pipeline.py` 中 `audit()`：对策略代码做结构化审计。
3. `services/decision/src/llm/gate_reviewer.py`：执行 L1 快审 / L2 深审，要求严格 JSON 输出。
4. `services/decision/src/research/yaml_signal_executor.py`：在 YAML 策略执行器里承担“代码生成 + 代码审核 + critic 复核”。

当前 researcher 侧 LoRA 数据集的核心目标是：财经新闻 / 研究报告 / 宏观语义 / 严格 JSON / 品种映射；这与 decision 侧“代码生成、代码审计、门控 JSON、PASS/FAIL 审核”属于不同任务分布。

若把两类任务在当前阶段强行混成一个 adapter，极易出现负迁移：

1. researcher 输出被代码任务污染，JSON 语气与字段稳定性下降。
2. decision 代码生成 / 审计被 researcher 样本分布拖偏，出现串味。
3. 后续无法独立回滚 researcher 与 decision 两端模型。

因此 decision 侧 qwen3 训练必须单独建任务，按独立数据集、独立 holdout、独立 adapter 推进。

## 目标
1. 为 decision 侧 qwen3 建立独立训练数据集，不与 researcher F4/F5 数据混训。
2. 优先强化以下 4 类能力：
   - 策略意图 -> Python 策略代码
   - 策略代码 -> 审计 JSON
   - L1/L2 门控上下文 -> 严格 JSON
   - YAML 策略执行器里的生成 / 审计 / critic 路径
3. 产出独立 decision adapter，建议目标 tag：`qwen3-decision:14b-q4_K_M`。
4. researcher 与 decision 两端维持“同一基座、不同 adapter”的隔离口径。
5. 为后续是否合并成多任务 adapter 提供可量化对比基线，但本任务不直接做统一训练。

## 数据范围（训练集候选）
1. `pipeline.research()` 的历史 intent / prompt / 代码输出样本。
2. `pipeline.audit()` 的代码输入 / 审计 JSON 样本。
3. `GateReviewer` 的 L1 / L2 prompt 与标准输出样本。
4. `yaml_signal_executor.py` 中生成、审核、PASS/FAIL 语料。
5. 已归档的策略 YAML、回测结果、审核意见、失败重试轨迹。
6. 必要时可追加少量高质量规则合成样本，但必须与真实历史样本分层标识。

## 明确排除（本任务不做）
1. 不修改 researcher 当前训练任务范围，不打断 Studio 正在进行的 F4/F5 训练。
2. 不直接把 `services/data/**` 的 researcher 训练语料并入 decision 训练集。
3. 不触碰 `shared/contracts/**`、`shared/python-common/**`、`.github/**`、`docker-compose.dev.yml`。
4. 不在本任务内同时实现“再训练触发监控”；监控另立独立任务。
5. 不做“统一一个 adapter 同时覆盖两端”的实施，只保留后续评估接口。

## 建议分批（供后续预审冻结）

### Batch A — decision 训练数据准备
- 候选范围：
  - `scripts/decision_finetune/prepare_dataset.py`（新建）
  - `scripts/decision_finetune/build_holdout.py`（新建）
  - `runtime/decision_finetune/**`（runtime，不入 git）
- 目标：提取 decision 历史样本、构造 train/val/holdout。

### Batch B — Studio LoRA 训练与导出
- 候选范围：
  - `scripts/decision_finetune/train_lora_mlx.sh`（新建）
  - `scripts/decision_finetune/export_to_ollama.sh`（新建）
  - `scripts/decision_finetune/deploy_model_to_studio.sh`（新建，可选）
- 目标：在 Studio 上对 `qwen3:14b-q4_K_M` 对应基座进行独立 LoRA 训练与导出。

### Batch C — decision 运行时切换与 A/B
- 候选范围：
  - `services/decision/src/llm/pipeline.py`
  - `services/decision/src/llm/gate_reviewer.py`
  - `services/decision/src/research/yaml_signal_executor.py`
  - `services/decision/.env.example`
- 目标：挂接新 decision adapter，完成 A/B 对照与回滚开关。

## 验收标准
1. `research()` 生成代码的 AST 语法通过率高于当前基线。
2. `audit()` 的 JSON 可解析率 >= 95%，关键字段完整率 >= 95%。
3. L1/L2 门控 JSON 可解析率 >= 98%。
4. `yaml_signal_executor.py` 的 qwen3 审核 PASS/FAIL 一致性高于当前基线。
5. 使用 decision adapter 后，不影响 researcher 现网模型与其回滚路径。
6. 形成独立 holdout 评估报告，可与当前线上 qwen3 基线直接对比。

## 建议启动时机
1. researcher 14B 训练、导出、部署、A/B 完成后，不直接启动本任务，而是先完成 researcher 7B 前筛训练与 researcher 链路闭环。
2. researcher 14B 与 researcher 7B 两条线均稳定后，再启动本任务的代码实施。
3. 在上述两条 researcher 训练线完成前，本任务只允许做只读盘点与样本归档，不进入写代码。
4. Studio 同一时间只跑一条 14B 训练链路；本任务不得与 researcher LoRA 同时抢占同一训练资源。

## 建议执行顺序
1. 先只读盘点 decision 侧历史样本与可复用评测集。
2. 由项目架构师补 PRE，冻结 Batch A 的最小白名单。
3. 先完成 holdout 基线，再训练，不允许“先训后补评测”。
4. 训练完成后仅在 decision 内做 A/B，确认收益后再考虑是否进入多任务统一评估。

## 风险与回滚
- 风险：decision 任务分布比 researcher 更复杂，纯规则合成样本过多会导致代码风格漂移。
- 风险：门控 JSON、代码生成、代码审计三类输出协议差异大，若标签不清，极易串任务。
- 回滚：运行时必须保留旧 `qwen3:14b-q4_K_M` 路径与环境变量开关，支持按服务独立回退。

## 备注
- 本任务的目标不是替代 researcher 训练，而是把 decision 侧 qwen3 的策略研发职责单独产品化、可训练化、可回滚化。
- 若未来 researcher 与 decision 都已拥有独立高质量数据集与 holdout，再另建任务评估“统一多任务 adapter”是否值得做。