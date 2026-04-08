# TASK-0021 H5 批 — decision_web rewrites 预审交接单

【签名】项目架构师
【时间】2026-04-08
【设备】MacBook

## 一、交接目标

把 `services/decision/decision_web/next.config.mjs` 从“`TASK-0021-H0` 白名单外历史脏改”正式收口为 `TASK-0021-H5` 单文件补充批次，供 Atlas、Jay.S 与决策 Agent 统一口径；当前只做预审与白名单冻结，不进入代码写入。

## 二、当前裁决

1. `services/decision/decision_web/next.config.mjs` 明确不属于 `TASK-0021-H0` 的 `Dockerfile` 单文件结论，也不并入 `H1`~`H4` 的后端业务批次。
2. 该文件当前 diff 语义只涉及 decision_web 到 decision 的前端 rewrites，不应继续以“白名单外历史脏改”悬空存在。
3. 因此正式冻结为：`TASK-0021-H5`，由决策 Agent 按单文件 P1 批次处理。

## 三、批次信息

- 任务 ID：`TASK-0021-H5`
- 执行 Agent：决策 Agent
- 保护级别：P1
- 是否需要 Token：需要单文件 P1 Token
- 是否可并行：可独立推进；不得与新的 decision_web 页面改动或部署批次混写

白名单：

1. `services/decision/decision_web/next.config.mjs`

## 四、本批次目的

1. 收口 decision_web → decision 的 `/api/decision/:path*` rewrites。
2. 冻结默认后端入口为 `http://localhost:8104`，并保留 `BACKEND_BASE_URL` 可覆盖机制。
3. 避免把该文件继续误算进 `H0`、部署批次或页面批次。

## 五、验收标准

1. `next.config.mjs` 只处理 `/api/decision/:path*` rewrites，不新增其他 rewrite、redirect 或 headers 逻辑。
2. 默认后端口径只允许是 `http://localhost:8104`，并允许 `BACKEND_BASE_URL` 覆盖。
3. 不扩展到 `Dockerfile`、`docker-compose.dev.yml`、`.env.example`、页面代码或后端代码。
4. `decision_web` 最小构建 / 诊断口径不因该文件报错。

## 六、执行约束

1. 本批次严格为单文件 P1；若实施中需要第 2 个业务文件，当前批次立即失效，必须回交补充预审。
2. 不得复用 `TASK-0021-H0` 的任何已锁回结论，也不得借用 `H1`~`H4` 的历史白名单。
3. 不得借本批次顺手改 `decision_web` 页面、Dockerfile、compose、`.env.example` 或后端 API。

## 七、向 Jay.S 汇报摘要

1. `services/decision/decision_web/next.config.mjs` 已正式从 `H0` 白名单外历史脏改收口为独立补充批次 `TASK-0021-H5`。
2. 当前只冻结 1 个业务文件：`services/decision/decision_web/next.config.mjs`。
3. 本批目标仅为 decision_web `/api/decision/*` rewrites 收口，不改 Dockerfile、compose、页面代码或后端代码。

## 八、下一步建议

1. 请 Jay.S 为决策 Agent 签发 `TASK-0021-H5` 的单文件 P1 Token。
2. 签发后，按单文件边界完成实现、自校验、终审与 lockback。
3. 在 Jay.S 未确认前，不派发决策 Agent 进入 `TASK-0021-H5` 代码写入。