# TASK-0129 — decision 历史生成目录清理与双端同步准备

【类型】P1 标准流程  
【建档】Atlas  
【日期】2026-04-26  
【状态】待项目架构师预审 → 待 Jay.S 文件级 Token 签发  
【执行 Agent】决策  
【服务边界】仅限 services/decision 单服务

## 1. 任务目标

在启动新的首批模板种子批量生成前，先清空 decision 下既有的历史生成目录，确保 MacBook 本地与 Studio 两端处于一致的干净基线。

目标固定为：

1. 不触碰 strategy_library 只读种子库。
2. 不触碰 Atlas_Import_Check.yaml。
3. 仅清理旧的 llm_generated / llm_ranked 及其 _tqsdk_runtime 镜像目录。
4. 清理后再作为后续 TASK-0128 的批量生成执行前置状态。
5. 若两端历史目录已一致，则不做无意义的“先同步旧产物再删除”。

## 2. 已确认事实

经只读核查，MacBook 本地与 Studio 当前历史 YAML 数量一致：

1. services/decision/strategies/llm_generated：17 个 YAML
2. services/decision/strategies/llm_ranked：4 个 YAML
3. services/decision/strategies/_tqsdk_runtime/llm_generated：1 个 YAML
4. services/decision/strategies/_tqsdk_runtime/llm_ranked：1 个 YAML

结论：

1. 当前旧产物在两端数量一致，先做“旧目录同步”没有新增价值。
2. 为保证后续生成干净，应直接清理上述四个历史目录及其伴随报告文件。
3. strategy_library、run_full_pipeline_35_symbols.py 与 shared/contracts 不属于本任务范围。

## 3. 本轮最小实现范围

本轮只做以下事项：

1. 清理 MacBook 本地 decision 历史生成目录。
2. 清理 Studio 上同名历史生成目录。
3. 做最小只读复核，确认四个目录已为空或已移除。
4. 为后续 TASK-0128 批量生成留出干净起点。

## 4. 清理目标目录

1. services/decision/strategies/llm_generated
2. services/decision/strategies/llm_ranked
3. services/decision/strategies/_tqsdk_runtime/llm_generated
4. services/decision/strategies/_tqsdk_runtime/llm_ranked

说明：

1. 本轮按目录清理，而不是只删 strategy.yaml，避免遗留 report.json、generation_report.json 等旧证据文件。
2. 不清理 services/decision/strategy_library/**。
3. 不清理 services/decision/strategies/Atlas_Import_Check.yaml。

## 5. 建议白名单（待预审冻结）

1. services/decision/strategies/llm_generated
2. services/decision/strategies/llm_ranked
3. services/decision/strategies/_tqsdk_runtime/llm_generated
4. services/decision/strategies/_tqsdk_runtime/llm_ranked

## 6. 明确排除项

1. services/decision/strategy_library/**
2. services/decision/scripts/**
3. shared/contracts/**
4. shared/python-common/**
5. runtime/**
6. logs/**
7. 任意真实 .env

## 7. 验收标准

1. 四个历史生成目录在 MacBook 本地被清理。
2. 四个历史生成目录在 Studio 被清理。
3. strategy_library 与 Atlas_Import_Check.yaml 未受影响。
4. 清理后两端 decision 进入可开始新一轮批量生成的干净状态。

## 8. 建议最小验证

1. 本地统计四个目录 YAML 数量为 0 或目录不存在。
2. Studio 统计四个目录 YAML 数量为 0 或目录不存在。
3. 抽查 Atlas_Import_Check.yaml 仍在。
4. 抽查 strategy_library 仍在。

## 9. 与 TASK-0128 的关系

1. TASK-0129 只负责清理旧生成目录，不实现新生成逻辑。
2. TASK-0128 继续负责“模板种子生成 + baseline + 筛选”的脚本实现与执行。
3. TASK-0129 完成后，TASK-0128 才进入真正批量生成执行面。