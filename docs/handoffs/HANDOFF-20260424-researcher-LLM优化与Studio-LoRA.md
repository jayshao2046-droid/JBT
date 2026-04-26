# HANDOFF — researcher LLM 优化与 Studio LoRA 微调（新窗口启动）

- 创建时间：2026-04-24
- 创建人：Atlas（主窗口）
- 接收方：新开 Atlas 子窗口（专责本批次）
- 主窗口去向：继续推进"数据-研报-消费"主线（daily_stats 接回 / macro 评分修正 / Decision 端验证）
- 模式：标准 P1 流程（PRE → Token → 实施 → 复核 → 终审 → Lockback）

---

## 一、新窗口要做的事

### 1. F1（Alienware 执行）— researcher LLM 参数收紧 + 两段式管线
- 任务文件：[docs/tasks/TASK-P1-20260424F1-researcher-LLM参数收紧与两段式管线.md](../tasks/TASK-P1-20260424F1-researcher-LLM参数收紧与两段式管线.md)
- 执行设备：MacBook 改代码 → rsync 同步 Alienware（17621@192.168.31.187）→ 重启 researcher 服务
- 责任 Agent：`数据`（services/data 归属）
- 白名单（7 文件）：
  1. `services/data/src/researcher/llm_analyzer.py`
  2. `services/data/src/researcher/kline_analyzer.py`
  3. `services/data/src/researcher/scheduler.py`（仅 `_call_macro_llm` 段 + stream cycle 钩子）
  4. `services/data/src/researcher/config.py`
  5. `services/data/src/researcher/prompts.py`
  6. **新增** `services/data/src/researcher/news_prefilter.py`
  7. `services/data/.env.example`
- 前置条件：Alienware 已后台拉取 `qwen2.5:7b-instruct-q4_K_M`（PID 287624，日志 `C:\Users\17621\ollama_pull_qwen25_7b.log`），新窗口接手时先确认 `ollama list` 已可见该模型再开工

### 2. F4 + F5 合并执行（Studio 24h 持续）— LoRA 微调 qwen3:14b
- 任务文件：
  - [docs/tasks/TASK-P1-20260424F4-Studio-QLoRA微调qwen3-14b固化JSON.md](../tasks/TASK-P1-20260424F4-Studio-QLoRA微调qwen3-14b固化JSON.md)
  - [docs/tasks/TASK-P1-20260424F5-qwen3-14b金融领域知识增强.md](../tasks/TASK-P1-20260424F5-qwen3-14b金融领域知识增强.md)
- 执行设备：MacBook 写脚本 → rsync 到 Studio（jaybot@192.168.31.142）→ Studio 24h 跑训练
- 责任 Agent：`数据`（统一在 Studio 上执行训练）
- 关键白名单（共用）：
  - 新增 `runtime/researcher_finetune/` 目录（不入 git）
  - 新增 `scripts/researcher_finetune/*.py` 与 `*.sh`
- 训练数据：D:\researcher_reports 历史 800+ 条 + FinGPT/finance-alpaca 2000+ 条 + 规则合成 1000+ 条 + 内部因子库术语 200 条
- **不限周末/夜间，Studio 100% 空转可全时占用**

---

## 二、新窗口执行顺序

```
Day 0  ┌─ 项目架构师对 F1 / F4 / F5 三单分别预审 → 出 REVIEW 文件
       └─ Jay.S 按白名单签 Token（建议三单一次性签发，但执行分轨）

Day 1  ├─ [Alienware 轨] F1 实施：改 7 文件 → 自校验 → rsync → 重启 → 验收
       └─ [Studio 轨]    F4+F5 数据准备：build_finance_corpus.py + merge_dataset.py

Day 2  ├─ [Alienware 轨] F1 验收后 Lockback + 独立提交
       └─ [Studio 轨]    LoRA 训练启动（mlx-lm，rank=32，epoch=5，24h 跑满）

Day 3-5 [Studio 轨] 训练 + 量化 + 打包 → ollama create qwen3-jbt-news:14b-q4_K_M

Day 6  [Alienware 轨] 推送新模型 → A/B 切换（保留旧模型 30 天）

Day 7-13 [A/B 观察]  → 通过验收 → F4+F5 Lockback + 独立提交
```

---

## 三、给新窗口 Atlas 的开工指令模板

> 你是新开的 Atlas 子窗口，专责执行 researcher LLM 优化与 Studio LoRA 微调批次。
>
> **第一步**：依次读取以下文件
> 1. `WORKFLOW.md`
> 2. `CLAUDE.md`
> 3. `docs/handoffs/HANDOFF-20260424-researcher-LLM优化与Studio-LoRA.md`（本文件）
> 4. `docs/tasks/TASK-P1-20260424F1-researcher-LLM参数收紧与两段式管线.md`
> 5. `docs/tasks/TASK-P1-20260424F4-Studio-QLoRA微调qwen3-14b固化JSON.md`
> 6. `docs/tasks/TASK-P1-20260424F5-qwen3-14b金融领域知识增强.md`
>
> **第二步**：用 subagent 调用"项目架构师"对 F1 / F4 / F5 三单分别做正式预审，产出 REVIEW 文件并冻结白名单。
>
> **第三步**：向 Jay.S 汇报预审结论，请求三单 Token 签发。
>
> **第四步**：Token 到位后，用 subagent 调用"数据" Agent 执行 F1 实施（Alienware 轨）；同时本窗口直接驱动 F4+F5 数据准备（Studio 轨）。
>
> **第五步**：F1 验收 → Lockback → 独立提交；F4+F5 训练完成 → A/B → Lockback → 独立提交。
>
> **关键约束**：
> - 不修改主窗口正在推进的 `services/decision/**` 与 `services/data/src/researcher/daily_stats.py`（属于主窗口 F2/F3 范围）
> - 不动 Mini 上任何文件
> - 严格遵守 CLAUDE.md 的"Mini 数据节点只读规则"
> - 每个批次完成后必须先向 Jay.S 汇报并等待确认
>
> **状态报告频率**：每个里程碑（预审完成 / Token 签发 / F1 实施完成 / 训练启动 / 训练完成 / A/B 启动 / 切换完成）都要主动汇报一次。

---

## 四、主窗口（本窗口）继续推进的工作

主窗口在新窗口跑 F1/F4/F5 期间，独立推进"数据-研报-消费"主线收口：

| 待办 | 说明 |
|---|---|
| **F2**：stream cycle 接回 daily_stats | 解决评估盲区（任务文件待建） |
| **F3**：Decision macro 评分识别 source_report.data_coverage | 解决评分失真（任务文件待建） |
| 持续监控 | researcher 当前生产运行态、Decision 三类 fact 入库情况 |

新窗口执行 F1 时会改 `services/data/src/researcher/scheduler.py`，**主窗口在 F1 完成 Lockback 之前不动 scheduler.py**，避免冲突。F2 改的也是 scheduler.py，因此 F2 必须排在 F1 之后串行执行。

---

## 五、风险提示
1. **设备并发风险**：F1 实施期间 Alienware 上的 researcher 服务会重启，会短暂中断研报生成（≤2 分钟）；F4 训练期间 Studio CPU/GPU 满载，decision/dashboard 服务延迟可能上升 → 需提前告知 Jay.S。
2. **代码冲突风险**：F1 与 F2 都改 scheduler.py，必须串行，绝不并行。
3. **凭据风险**：F5 数据下载若涉及 HuggingFace token，必须放 .env 不入 git。
4. **训练失败回滚**：保留旧 qwen3:14b 30 天，env 一行回切。

---

## 六、Atlas 主窗口签字
- 创建：Atlas（2026-04-24）
- 待 Jay.S 确认后正式启用新窗口
