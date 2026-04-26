# TASK-P1-20260425H1 — researcher 7B 前筛模型独立训练

## 任务类型
- P1 标准流程
- 服务归属：services/data（researcher 两段式链路）
- 协同设备：Alienware（优先训练 + 部署验证），Studio（仅作回退训练备选）
- 当前状态：仅建档，待项目架构师预审；未冻结文件白名单，未申请 Token
- 启动前提：researcher 14B 新模型完成训练、导出、部署与首轮 A/B 验证后，再启动本任务实施

## 背景与根因
当前 researcher 主链路已冻结为：

1. 7B 负责前置筛选。
2. 14B 负责深分析与最终报告。

但目前 7B 仍是通用基座，尚未针对 JBT researcher 的真实分布做过独立训练，存在以下问题：

1. 对重复转载、弱相关资讯、噪声快讯的过滤不够稳。
2. 对期货/宏观/商品链路里的“应放行高价值资讯”与“应拦截噪声资讯”边界仍偏粗。
3. 若直接把 researcher 14B 训好而 7B 维持通用基座，则两段式链路仍不完整，后续无法稳定比较“前筛收益 vs 深分析收益”。

因此 researcher 7B 必须作为独立训练任务落地，但顺序上必须后置于 researcher 14B。

## 目标
1. 为 researcher 前筛模型建立独立训练集，不与 14B 深分析输出协议混训。
2. 强化 7B 在以下场景中的判断能力：
   - 新闻/快讯相关性打分
   - 噪声转载识别
   - 品种/宏观主题命中
   - 是否值得进入 14B 深分析的放行判断
3. 产出 researcher 7B 独立模型或 adapter，供 Alienware 本地前筛使用。
4. 在 researcher 14B 已上线后，再用该 7B 替换现有通用前筛模型，形成 researcher 完整两段式闭环。

## 设备分工（当前建议）
| 设备 | 角色 | 说明 |
|---|---|---|
| Alienware (192.168.31.187) | 优先训练 + 最终部署 | sim 未开启期间，可暂停 researcher 运行态，把 7B 训练与验证放在本机完成 |
| Studio (192.168.31.142) | 仅备选训练机 | 仅当 Alienware 训练稳定性或显存不足无法闭环时再作为回退 |
| MacBook | 数据准备 + 协调 | 构造训练集、评测集、记录验收证据 |

## 明确边界
1. 本任务只针对 researcher 7B 前筛，不覆盖 Studio decision 门控。
2. 不把 decision/gate/YAML 审核样本混入 7B 训练集。
3. 不与 researcher 14B 同时抢占同一训练资源。
4. 不在 sim 开启期间执行 Alienware 7B 训练。
5. 不直接修改 Mini 上任何文件。

## 数据范围（候选）
1. 已归档 researcher 新闻样本中“被 14B 深分析后证明高价值”的正样本。
2. 已归档 researcher 流程里的转载、弱相关、低评分噪声样本。
3. 宏观/商品/期货主题的人工校正样本。
4. researcher 前筛日志与放行结果（若有留痕）。
5. 小规模规则合成样本，仅用于补齐边界，不作为主样本来源。

## 建议分批（供后续预审冻结）

### Batch A — researcher 7B 数据准备
- 候选范围：
  - `scripts/researcher_finetune/build_prefilter_corpus.py`（新建）
  - `scripts/researcher_finetune/build_prefilter_holdout.py`（新建）
  - `runtime/researcher_finetune/**`（runtime，不入 git）
- 目标：构造 7B 前筛 train/val/holdout 数据集。

### Batch B — Alienware 7B 训练与导出
- 候选范围：
  - `scripts/researcher_finetune/train_prefilter_7b.sh`（新建）
  - `scripts/researcher_finetune/export_prefilter_7b.sh`（新建）
- 目标：在 Alienware 本机优先完成 7B 训练与导出。

### Batch C — researcher 运行时切换与 A/B
- 候选范围：
  - `services/data/src/researcher/config.py`
  - `services/data/.env.example`
  - `services/data/src/researcher/news_prefilter.py`
- 目标：接入新 7B，保留回滚开关，完成 researcher 两段式 A/B。

## 验收标准
1. 7B 前筛在固定 holdout 上的高价值资讯召回率不低于当前通用基座。
2. researcher 单轮进入 14B 深分析的新闻比例继续下降，且不因过筛过严丢失明显高价值样本。
3. researcher 全链路总耗时较当前进一步下降，或在相同耗时下提高有效报告质量。
4. Alienware 本地可稳定加载新 7B，不影响 researcher 14B 已上线模型。
5. researcher 7B 与 14B 共同运行时无持续 OOM 或明显吞吐崩溃。

## 建议启动时机
1. researcher 14B 新模型部署并完成首轮 A/B 验证后立即启动。
2. sim-trading 未开启期间优先执行。
3. 若 Alienware 后续进入 sim 交易窗口，本任务自动让位，不与交易时段抢资源。

## 风险与回滚
- 风险：Alienware RTX 2070 8GB 在 Windows 环境下做 7B 训练稳定性不足。对策：先做短程试训，失败则回退到 Studio 执行。
- 风险：7B 为追求过滤率而损伤高价值资讯召回。对策：holdout 必须包含“应放行”难例，不允许只看过滤率。
- 回滚：保留现有通用前筛模型与 `OLLAMA_PREFILTER_ENABLED` / 模型名切换开关，一键回退。

## 备注
- 本任务的目标是补齐 researcher 两段式链路，而不是让 7B 替代 14B。
- researcher 14B 与 researcher 7B 完成后，才进入 Studio 14B（decision/gate）独立训练阶段。