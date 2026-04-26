# TASK-P1-20260424F4 — Studio QLoRA 微调 qwen3:14b 固化 JSON

## 任务类型
- P1 标准流程
- 服务归属：跨设备工程任务（Studio 训练 + Alienware 部署），不直接动 services/** 业务代码
- 母任务：TASK-P1-20260424F1（F1 在 Alienware 上线后立即启动本单，不再等 14 天）
- 当前状态：可进入 Jay.S 文件级 Token 签发与实施（Studio 端独立执行，不阻塞主线）
- 执行模式：Studio 24h 持续训练（模拟交易未开盘，Studio 100% 空转，无需限制周末/夜间）

## 背景
F1 完成"参数收紧 + 两段式管线"后，14B 深分析的延迟与噪声问题基本解决，但仍有两个长期收益项需要靠 LoRA 微调拿下：

1. **JSON schema 漂移**：qwen3:14b 偶发会输出多余字段或字段缺失，下游解析需要兜底
2. **think 链习惯**：即使 prompt 加 `/no_think`，模型仍偶尔输出推理段，浪费 token
3. **期货品种命中率**：通用模型对 SHFE/DCE/CZCE/CFFEX 品种代码与中文俗名的对应关系有时混淆

QLoRA 窄域微调能把这三项固化进权重，预期质量 +10–20%，但**不解决延迟问题**（延迟靠 F1 解决）。

## 目标
1. 在 Studio（M2 Max 32GB）上用 mlx-lm 跑 LoRA 微调，目标模型 qwen3:14b（基础权重，非量化）。
2. 训练数据来源（不再等待生产积累）：
   - **A. 历史存量**：D:\researcher_reports\ 下 4/15 起所有已生成 NEWS/MACRO/FUTURES JSON 报告（估算 ≥ 800 条可用样本）
   - **B. 公开金融语料**：FinGPT/finance-alpaca 等开源中文金融指令集，过滤为期货/宏观/商品相关（≥ 2000 条）
   - **C. 规则合成**：用 qwen3:14b 自身在 Studio 上离线批量生成"标准答案 JSON"，再人工抽样校验 200 条
3. 训练完成后，把 LoRA adapter 合并回基础权重 → 重新量化为 q4_K_M → 通过 ollama create 打包为 `qwen3-jbt-news:14b-q4_K_M`。
4. 部署回 Alienware 替换原 qwen3:14b（保留旧模型 7 天用于 A/B）。
5. **本任务可与 F5（金融领域知识增强）合并训练数据集，统一一次 LoRA 跑完。**

## 设备分工
| 设备 | 角色 | 所需资源 |
|---|---|---|
| Studio (192.168.31.142, M2 Max 32GB) | LoRA 训练 + 量化打包 | mlx-lm, ollama, 50GB 磁盘 |
| Alienware (192.168.31.187, RTX 2070 8GB) | 微调后模型推理部署 | ollama 11434 |
| MacBook | 训练数据准备 + 跨设备协调 | rsync |

## 冻结白名单（数据 + 配置）
1. **新增目录**：`runtime/researcher_finetune/` — 训练数据集、训练脚本、checkpoint 临时目录（runtime/ 不入 git，不计 P0）
2. **新增脚本**：`scripts/researcher_finetune/prepare_dataset.py` — 从 D:\researcher_reports 抽取已生成报告 → 配对清洗 → 输出 jsonl
3. **新增脚本**：`scripts/researcher_finetune/train_lora_mlx.sh` — Studio 上 mlx-lm 训练命令封装
4. **新增脚本**：`scripts/researcher_finetune/export_to_ollama.sh` — LoRA 合并 + 量化 + ollama create
5. **新增脚本**：`scripts/researcher_finetune/deploy_model_to_nodes.sh` — 推送新模型到 Alienware（ollama push/scp）+ Studio（本地 ollama create），并验证两端 /api/tags 可见新模型；两端统一使用 qwen3-jbt-news:14b-q4_K_M（量化版）
6. **配置变更**：F1 上线后的 `services/data/src/researcher/config.py` 仅在最终切换时改一行 `OLLAMA_MODEL`（独立小批次）；Studio decision gate_reviewer.py / researcher_qwen3_scorer.py 的 MODEL 切换同样走独立后置小批次

## 明确排除
1. F1 完成前不动任何文件
2. 不修改 services/data 任何业务代码（仅最终切换 OLLAMA_MODEL 一行，走独立小批次）
3. 不动 shared/contracts、shared/python-common
4. 不动 Mini 上任何文件
5. 不在 Alienware 上跑训练（显存不够 + 影响生产）

## 验收标准
1. Studio 完成 LoRA 训练，loss 收敛，输出 adapter 文件
2. 合并 + 量化后的新模型 `qwen3-jbt-news:14b-q4_K_M` 在 Alienware 可加载
3. 100 条 holdout 新闻测试集上：
   - JSON 解析成功率 ≥ 99%（基线 ~90%）
   - 期货品种命中率 ≥ 95%（基线 ~80%）
   - think 链出现率 ≤ 1%（基线 ~30%）
4. 单条推理延迟与基线相当或更低（不退化）
5. A/B 一周后无生产事故，正式切换 OLLAMA_MODEL

## 时间盒（24h 持续模式，Studio 全时占用）
- 数据准备（含 F5 金融语料合并）：1–2 天
- LoRA 训练：Studio M2 Max 24h 持续，预计 6–12 小时（rank=16, epoch=3, batch=4）；可直接 epoch=5 跑满
- 量化 + 打包 + 推送 Alienware：半天
- A/B 观察：3–7 天
- 总计：F1 上线后约 5–10 天完成切换
- **不限制周末/夜间**：Studio 当前 100% 空转，可 24h 持续训练
- **不阻塞数据-研报-消费主线**：本任务在独立窗口/独立会话执行

## 风险与回滚
- **风险**：历史 800 条多样性不足导致过拟合。**对策**：必须并入 F5 金融语料 + 规则合成 ≥ 3000 条；用 holdout 100 条监控 val_loss。
- **风险**：M2 Max mlx-lm 与 qwen3 兼容性问题。**对策**：备选 unsloth + 租 4090 4 小时（¥40）。
- **风险**：Studio 24h 长跑过热降频。**对策**：第一轮 2h 后查 powermetrics，必要时降 batch 或加散热间隔。
- **回滚**：保留旧 qwen3:14b，env 一行回切；旧模型保留 30 天。

## 关联依赖
- 强依赖：TASK-P1-20260424F1 在 Alienware 上线（提供基线对照）
- 强依赖：TASK-P1-20260424F5（金融语料增强，**与本单合并训练**）
- 弱依赖：TASK-P1-20260424F2（daily_stats 接回，便于评估训练效果）

## 备注
本单当前为 **PRE 占位**，F1 完成后由 Atlas 重新触达项目架构师做正式预审与白名单冻结。
