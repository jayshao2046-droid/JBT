# REVIEW-TASK-0129 — decision 历史生成目录清理与双端同步准备

【审核角色】项目架构师  
【审核阶段】FINAL 终审  
【日期】2026-04-26  
【状态】passed_allow_lockback  
【关联 token】tok-79b0d20d-0eca-44a8-a551-8eb75aed13ee  
【关联 lock review_id】REVIEW-TASK-0129

## 1. 终审结论

通过终审，可执行 lockback。

本次终审以用户已确认的实施与双端验证事实为准。当前可以裁定：本轮实际清理严格收敛在 4 个历史目录内，且实际执行面比 PRE 授权更窄，仅删除历史 YAML 并清理清理后形成的空子目录；`services/decision/strategies/Atlas_Import_Check.yaml` 保留，未见越界到 `services/decision/scripts/**`、`shared/contracts/**`、`shared/python-common/**` 或任一策略源库写入。

## 2. 实际审查范围

本次终审仅审以下 4 个历史目录对应的清理动作：

1. `services/decision/strategies/llm_generated`
2. `services/decision/strategies/llm_ranked`
3. `services/decision/strategies/_tqsdk_runtime/llm_generated`
4. `services/decision/strategies/_tqsdk_runtime/llm_ranked`

本轮实际执行内容收口为：

1. 删除上述 4 个目录中的历史 YAML。
2. 删除清理后形成的空子目录。
3. 不新增其他目录改写，不新增脚本改动，不触碰策略源库。

## 3. 双端验收事实

### 3.1 MacBook 本地

已确认以下事实：

1. 上述 4 个历史目录中的 YAML 数量均为 0。
2. `services/decision/strategies/Atlas_Import_Check.yaml` 仍在。
3. `services/decision/strategy_library` 仍在，且本地仍保留 804 个 YAML。

### 3.2 Studio 远端

已确认以下事实：

1. 上述 4 个历史目录中的 YAML 数量均为 0。
2. `services/decision/strategies/Atlas_Import_Check.yaml` 仍在。
3. 本轮未确认任何白名单外目录被删除或改写。

## 4. 环境偏差裁定

本轮终审需明确一项环境偏差：Studio 端并不存在 `services/decision/strategy_library` 目录，实际保留的是旧路径 `services/decision/参考文件/因子策略库/入库标准化` 及其上层目录。

对此裁定如下：

1. 该差异属于 Studio 端既有环境现状，不是本次 `TASK-0129` 清理动作造成的结果。
2. 因此，PRE 中“Studio 上 `strategy_library` 仍在”的验证项与远端现状不一致，但该不一致不构成本次清理越界，也不构成误删证据。
3. 本次 FINAL 终审的有效关注点应收口为：4 个历史目录清零、`Atlas_Import_Check.yaml` 保留、且未扩展到白名单外路径。

## 5. Lockback 裁定

1. 是否允许 lockback：是。
2. 是否要求新增代码修改：否。
3. 是否要求补充新的服务侧实现：否。
4. 本次 lockback 不要求调整既有任务边界；仅按已完成事实收口。

建议 lockback 摘要：

`TASK-0129 终审通过；MacBook 与 Studio 四个历史目录 YAML 已清零，Atlas_Import_Check.yaml 保留，Studio 缺少 strategy_library 属既有环境差异而非本次误删，允许 lockback。`

## 6. 审核意见

1. 本轮终审不要求任何新增代码修改。
2. 若后续需要在 Studio 端读取策略模板源，应按 `TASK-0128` 补充 PRE 中的“只读自动探测模板源目录”口径执行，不回写本任务范围。
