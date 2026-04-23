# TASK-P1-20260423D3 — decision .env.example 补齐 researcher URL

## 任务类型
- P1 标准流程
- 服务边界：仅 `services/decision/.env.example`
- 当前状态：已完成，已锁回（2026-04-23）

## 任务来源
- 来源母任务：`TASK-P1-20260423D`
- 预审依据：`docs/reviews/REVIEW-TASK-P1-20260423D-decision直连Alienware-researcher链路收敛-PRE.md`

## 根因
- decision 当前缺少 researcher 专用 URL 的配置样例说明，导致 `DATA_SERVICE_URL` 被继续误用为 researcher 报告源。
- `services/decision/.env.example` 属于 P0 保护路径，必须独立签发，不能与 decision 代码批次合并。

## 目标
1. 在 `.env.example` 中补齐 researcher 专用 URL 配置说明。
2. 默认值与当前运行态口径一致，指向 Alienware `:8199`。
3. 本批只处理 researcher URL 相关说明，不顺手改其他配置项。

## 冻结白名单
- `services/decision/.env.example`

## 明确排除
- `services/decision/src/**`
- 其他任意 `.env.example`
- `docker-compose.dev.yml`

## 验收标准
1. `.env.example` 中明确存在 researcher 专用 URL 配置项。
2. 默认值指向 Alienware `http://192.168.31.223:8199`。
3. 未引入与 researcher URL 无关的其他配置改动。

## 约束
- 本文件属于 P0 保护路径，只能单文件单独签发。