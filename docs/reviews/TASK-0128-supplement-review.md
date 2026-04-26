# REVIEW-TASK-0128-SUPPLEMENT — decision 特征模板多周期批量生成与基线筛选

【审核角色】项目架构师  
【审核阶段】SUPPLEMENT PRE 补充预审  
【日期】2026-04-26  
【状态】approved_for_token

## 1. 补审原因

`TASK-0128` 现有 PRE 已批准脚本与窄测，但不足以覆盖后续运行时输出目录，也未纳入 Studio 端模板源目录与本地目录结构不一致这一实现层事实。

本次补审只补齐以下两项：

1. 新增允许写入的 `template_seed_*` 输出目录边界。
2. 新增脚本“只读自动探测模板源目录”的环境兼容口径。

## 2. 补充预审结论

通过，可按 decision 单服务标准流程补充 Token 范围。

本次补审后的执行边界固定为：

1. 继续保留原 PRE 对脚本与窄测的批准。
2. 新增允许写入范围仅限 3 个 `template_seed_*` 输出目录。
3. 允许脚本只读探测模板源目录，但不授权修改任一模板源目录。
4. 不新增 `shared/contracts/**`、`shared/python-common/**`、其他 `services/**`、`runtime/**`、`logs/**` 或真实 `.env` 范围。

## 3. 补充后冻结白名单口径

### 3.1 继续沿用既有业务文件

1. `services/decision/scripts/run_template_seed_baseline_pipeline.py`
2. `services/decision/tests/test_template_seed_baseline_pipeline.py`

### 3.2 新增允许写入的输出目录

1. `services/decision/strategies/template_seed_generated`
2. `services/decision/strategies/template_seed_reports`
3. `services/decision/strategies/template_seed_tuning_candidates`

## 4. 只读模板源探测规则

脚本可执行只读自动探测模板源目录，规则固定如下：

1. 优先使用 `services/decision/strategy_library`。
2. 若上述目录不存在，则回退到 `services/decision/参考文件/因子策略库/入库标准化`。
3. 上述规则仅授权“存在性探测 + 只读读取模板”。
4. 不授权修改、重命名、迁移、删除或覆盖 `strategy_library` 与 `参考文件/因子策略库/入库标准化` 中的任何文件。
5. 不授权在两条模板源路径的父目录内新增中间产物。

## 5. 明确排除项

1. `services/decision/scripts/run_full_pipeline_35_symbols.py`
2. `services/decision/strategy_library/**` 的任何写操作
3. `services/decision/参考文件/因子策略库/**` 的任何写操作
4. `services/decision/strategies/llm_generated/**`
5. `services/decision/strategies/llm_ranked/**`
6. `shared/contracts/**`
7. `shared/python-common/**`
8. `services/data/**`
9. `services/backtest/**`
10. `services/dashboard/**`
11. `runtime/**`
12. `logs/**`
13. 任意真实 `.env`

## 6. 最小验证集

1. 当 `services/decision/strategy_library` 存在时，脚本优先从该路径读取模板。
2. 当 `services/decision/strategy_library` 不存在时，脚本能回退到 `services/decision/参考文件/因子策略库/入库标准化`，且只执行只读读取。
3. 全部运行期输出仅落在 `template_seed_generated`、`template_seed_reports`、`template_seed_tuning_candidates` 三个目录。
4. `strategy_library` 与 `参考文件/因子策略库/入库标准化` 下无原地修改。
5. 原 PRE 约束继续生效：新脚本不回到 `OpenAICompatibleClient` / `CodeGenerator` / `llm_generated` / `llm_ranked` 首批生成入口。

## 7. 对 TASK-0128 Lock 的最小白名单建议

当前 `docs/locks/TASK-0128-lock.md` 仅覆盖脚本与窄测，若要支撑真实运行写盘，建议最小 Allowed Files 范围补充为以下 5 项边界：

1. `services/decision/scripts/run_template_seed_baseline_pipeline.py`
2. `services/decision/tests/test_template_seed_baseline_pipeline.py`
3. `services/decision/strategies/template_seed_generated`
4. `services/decision/strategies/template_seed_reports`
5. `services/decision/strategies/template_seed_tuning_candidates`

同时明确：

1. 上述 3 个输出目录只用于表达最小执行边界，不得被解释为目录级通配解锁。
2. Jay.S 实际签发 Token 时，仍应按 `lockctl` 当前能力，将一次运行会创建、覆盖或回写的具体文件清单收口为文件级最小列表。
3. 本次补审不直接修改 `TASK-0128` lock 文件。

## 8. 审核意见

1. 本次补审只补齐输出目录与只读模板源探测，不改变 `TASK-0128` “首批不走在线模型生成”的主目标。
2. 两条模板源路径均只可读，不可写。
3. 若实施中证明仍需新增白名单文件或新增输出路径，必须回项目架构师继续补充预审。
