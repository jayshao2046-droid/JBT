# TASK-0120 预审记录

【预审人】项目架构师（Livis）  
【日期】2026-04-15  
【状态】预审通过

## 1. 服务边界

- 允许范围：`services/data/**`、`services/decision/**`（按白名单）
- 禁止范围：`shared/contracts/**`、`shared/python-common/**`、`WORKFLOW.md`、`.github/**`

## 2. 白名单审查

- 白名单共 32 文件，覆盖研究中心上线链路与决策通知收口必需最小集。
- 无跨服务 import 规则违规前提（按实现阶段再验）。

## 3. 风险提示

1. data 与 decision 同时改动，需严格以测试和运行态证据收口。
2. 通知通道可能受环境变量影响，必须做实发验证。
3. 研究中心“有落档”不等于“可收口”，需内容有效性门槛。

## 4. 结论

预审通过，允许 Atlas 为 Claude 签发 TASK-0120 一次性总 Token。
