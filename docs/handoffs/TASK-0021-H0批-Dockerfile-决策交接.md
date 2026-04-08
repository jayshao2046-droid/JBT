# TASK-0021 H0 批 — decision_web Dockerfile 构建收口交接单

【签名】决策 Agent  
【交接时间】2026-04-08  
【review_id】REVIEW-TASK-0021-H0  
【token_id】tok-2ae91304-d52b-4e09-b434-fdef71fc086b

---

## 执行结果摘要

**状态：已完成，待项目架构师终审与 lockback**

---

## 任务信息

- 任务 ID：TASK-0021-H0
- 执行范围：`services/decision/decision_web/Dockerfile` 单文件 P0 白名单
- 批次目标：修复 decision_web 生产构建阻塞，移除非法 `COPY` shell 重定向写法

---

## 变更文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/decision_web/Dockerfile` | 最小修改 | builder 阶段显式创建 `public` 目录，runner 阶段改回合法 `COPY` |
| `docs/prompts/agents/决策提示词.md` | 更新 | 同步 H0 状态、自校验结果与后续等待事项 |

---

## 改动说明

1. 保持原有 deps / builder / runner 三阶段结构不变。
2. 将 builder 阶段的 `RUN npm run build` 收口为 `RUN mkdir -p public && npm run build`，确保仓内当前没有 `public/` 目录时，镜像构建阶段仍存在合法复制源路径。
3. 将 runner 阶段的非法写法 `COPY --from=builder /app/public ./public 2>/dev/null || true` 改为合法 Dockerfile 语义 `COPY --from=builder /app/public ./public`。
4. 未扩展到 `docker-compose.dev.yml`、`.dockerignore`、`next.config.mjs`、页面代码或其他服务文件。

---

## 验证结果

1. `services/decision/decision_web/Dockerfile` 执行 `get_errors` 结果为 `No errors found`。
2. 已执行：`docker build -t jbt-decision-web-task-0021-h0 services/decision/decision_web`。
3. 构建结果：**成功**。关键链路已确认：
   - builder 阶段 `RUN mkdir -p public && npm run build` 通过；
   - runner 阶段 `COPY --from=builder /app/public ./public` 通过；
   - 原先非法 `COPY ... 2>/dev/null || true` 不再阻断构建。

---

## 待审问题

1. 本机构建输出存在 3 条非阻断 warning：基础镜像当前以 `linux/amd64` 被拉取，而宿主为 `arm64`。这不影响本批次“修复非法 COPY 构建阻塞”的验收结论。
2. 若后续要进一步统一多架构镜像语义或补充显式 `platform` 策略，应另起补充预审，不在 H0 单文件范围内处理。

---

## 向 Jay.S 汇报摘要

1. `TASK-0021-H0` 已按单文件白名单完成，`decision_web` Dockerfile 中的非法 `COPY` shell 重定向写法已移除。
2. 本次为最小改动，只在 builder 阶段补了 `mkdir -p public`，并把 runner 阶段改成合法 `COPY`，没有扩展到 compose、前端页面或其他服务文件。
3. 已完成与改动直接相关的自校验：Dockerfile 诊断为 0，完整 `docker build` 成功，生产镜像构建不再卡在 `COPY /app/public`。

---

## 下一步建议

1. 进入项目架构师终审；若通过，立即按 `REVIEW-TASK-0021-H0` 执行 lockback。
2. 在 Jay.S 未确认前，不自动进入 `TASK-0021-H1`、`H2`、`H3`、`H4`。
