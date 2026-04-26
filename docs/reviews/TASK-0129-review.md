# REVIEW-TASK-0129 — decision 历史生成目录清理与双端同步准备

【审核角色】项目架构师  
【审核阶段】PRE 预审  
【日期】2026-04-26  
【状态】approved_for_token

## 1. 服务边界裁定

该事项属于 services/decision 单服务闭环，可按标准流程申请 Token。

依据：

1. 本轮目标仅为清理 decision 历史生成目录，并做双端最小只读复核。
2. 不涉及 shared/contracts、shared/python-common 或其他服务目录。
3. 不要求改写 strategy_library、脚本入口、运行态目录或真实环境文件。

## 2. 预审结论

通过。当前只批准“历史生成目录清理 + 双端最小只读复核”这一最小闭环。

1. 允许执行 Agent 按标准流程申请 Token。
2. 预审冻结的最小执行面仅限以下四个历史目录，不得扩展到其他 decision 路径。
3. 当前冻结的是目录级执行边界，不代表目录级通配解锁；Jay.S 实际签发时，仍须按 lockctl 当前能力落为目录内现存目标文件的文件级最小清理白名单。

## 3. 冻结的最小白名单范围

1. services/decision/strategies/llm_generated
2. services/decision/strategies/llm_ranked
3. services/decision/strategies/_tqsdk_runtime/llm_generated
4. services/decision/strategies/_tqsdk_runtime/llm_ranked

## 4. 明确排除项

1. services/decision/strategy_library/**
2. services/decision/scripts/**
3. services/decision/strategies/Atlas_Import_Check.yaml
4. shared/contracts/**
5. shared/python-common/**
6. runtime/**
7. logs/**
8. 任意真实 .env

## 5. 最小验证集

1. MacBook 本地四个目标目录中的 YAML 数量为 0，或目录已不存在。
2. Studio 上同名四个目标目录中的 YAML 数量为 0，或目录已不存在。
3. services/decision/strategies/Atlas_Import_Check.yaml 仍在。
4. services/decision/strategy_library/** 仍在且未受影响。

## 6. 审核意见

1. TASK-0129 只负责清理旧生成目录，不包含新一轮生成、baseline、筛选或调优逻辑。
2. 若实施中需要触碰 strategy_library、scripts、shared/contracts、runtime、logs、真实 .env 或新增其他目录，必须回项目架构师补充预审。