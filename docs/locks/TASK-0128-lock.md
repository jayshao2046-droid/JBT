# TASK-0128 Lock Record

- task_id: TASK-0128
- service: decision
- agent: 决策
- review_id: REVIEW-TASK-0128-SUPPLEMENT
- token_id: tok-38088590-374e-4360-ac9d-3d710c66aa7f
- status: active
- issued_at: 2026-04-26 02:44:09 CST
- expires_at: 2026-04-26 04:44:09 CST
- ttl: 120 minutes
- reason: 为 decision 新增“特征模板多周期批量生成 + baseline 筛选”脚本，首批不走在线模型生成

## Allowed Files
- services/decision/scripts/run_template_seed_baseline_pipeline.py
- services/decision/tests/test_template_seed_baseline_pipeline.py

## Run Batch Token（运行批）
- token_id: tok-bf761640-79c8-4ecc-95fb-5494e069a700
- issued_at: 2026-04-26 03:08:46 CST
- expires_at: 2026-04-26 11:08:46 CST（TTL 480min）
- files: services/decision/.gitignore, services/decision/strategies/template_seed_reports/summary.json, services/decision/strategies/template_seed_tuning_candidates/manifest.json

## Notes
- 脚本实现批 token（tok-38088590）覆盖脚本与窄测 2 个显式文件，已完成。
- 运行批 token（tok-bf761640）覆盖 .gitignore 与两个 manifest 文件；产物目录已通过 .gitignore 屏蔽，无需逐文件签发。
- DEFAULT_DATA_URL 已修正为 192.168.31.74（Mini 真实 IP）。
- 本批不得把 run_full_pipeline_35_symbols.py、llm_generated/llm_ranked、strategy_library 源 YAML、参考文件/因子策略库源 YAML、shared/contracts 或其他 decision 文件并入。
- 脚本允许只读探测模板源目录：优先 `services/decision/strategy_library`，不存在时回退 `services/decision/参考文件/因子策略库/入库标准化`；两条路径均不得写入。
- Jay.S 实际签发 Token 时，仍须按 lockctl 当前能力，将单次运行会创建、覆盖或回写的具体文件清单收口为文件级最小列表。
- 执行 Agent 固定为“决策”；Atlas 只负责建档、签发推进、验收与锁回，不代写 decision 业务代码。
- 当前阶段只完成“模板种子生成 + baseline + 筛选 + 回传 MacBook”，不启动 LLM 自动化调优。
- 若实施中需要新增白名单文件，必须先回项目架构师补充预审。