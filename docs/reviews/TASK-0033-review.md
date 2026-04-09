# TASK-0033 Review

## Review 信息

- 任务 ID：TASK-0033
- 审核角色：项目架构师预审 + Atlas 终审
- 审核阶段：A 批终审通过，B 批待签发
- 审核时间：2026-04-09
- 当前结论：A 批终审通过并已 lockback，B 批可在签发后继续

---

## 一、预审范围

1. 评估 `data_web` 从临时原型升级为 data 单服务正式化看板是否可继续。
2. 冻结 A / B 两批的最小白名单与明确排除项。
3. 冻结本轮远端拉页方式为 data_web 独立前端容器，不修改根编排。

## 二、预审结论

1. `TASK-0033` 可继续，但必须严格保持 data 单服务边界。
2. 当前问题不在页面骨架，而在 `8105` 现有接口面不足以支撑六个 data 视图，需要先做 A 批只读接口收口，再做 B 批前端正式化。
3. 本轮不得把 Collectors / Settings 等页面顺手升级为在线运维控制台；缺少安全写接口支撑的控件必须保持只读、隐藏或禁用。

## 三、批次与白名单

### A 批：8105 数据面只读接口收口

1. `services/data/src/main.py`
2. `services/data/tests/test_main.py`

状态：`pending_token`

终审结果：

1. 已完成 `main.py` / `test_main.py` 两文件内的 4 个只读聚合接口收口。
2. 已按终审意见去除绝对路径、主机指纹、配置值、调度原始 endpoints 与未脱敏日志内容。
3. 本地验证：两文件 `get_errors = 0`；`pytest services/data/tests/test_main.py -q` = `6 passed`。
4. 第三次只读终审结论：无阻断发现，可进入 lockback。
5. lockback 留痕：token_id=`tok-836bb68d-91b7-460d-ad28-f2905aa7b7dd`，review_id=`REVIEW-TASK-0033-A`，状态=`locked`。

### B 批：3004 前端正式化与独立前端容器

1. `services/data/data_web/app/page.tsx`
2. `services/data/data_web/components/pages/overview-page.tsx`
3. `services/data/data_web/components/pages/collectors-page.tsx`
4. `services/data/data_web/components/pages/data-explorer-page.tsx`
5. `services/data/data_web/components/pages/news-feed-page.tsx`
6. `services/data/data_web/components/pages/system-monitor-page.tsx`
7. `services/data/data_web/components/pages/settings-page.tsx`
8. `services/data/data_web/next.config.mjs`
9. `services/data/data_web/package.json`
10. `services/data/data_web/Dockerfile`

状态：`pending_token`

## 四、明确排除

1. `shared/contracts/**`
2. `docker-compose.dev.yml`
3. 所有环境样例文件与真实环境文件
4. 所有非 data 服务目录
5. `services/data/data_web/app/agent-network/page.tsx`
6. `services/data/data_web/app/command-center/page.tsx`
7. `services/data/data_web/app/intelligence/page.tsx`
8. `services/data/data_web/app/operations/page.tsx`
9. `services/data/data_web/app/systems/page.tsx`

## 五、预审风险

1. 六页原型的信息密度明显大于当前 `main.py` 的真实接口面，若要求每个卡片与动作一比一做实，任务会快速膨胀。
2. 若把 Collectors / Settings 页面写接口一起做实，会越过“正式化看板”边界，漂移成在线运维系统。
3. 若新增读接口全部堆进 `main.py` 且无测试约束，后续维护成本会升高。
4. Mini 端若直接高频扫 parquet、日志与进程状态而不做轻量聚合，3004 首屏与刷新稳定性会受影响。

## 六、当前状态字段

1. `TASK-0033`：`a_locked_b_pending_token`
2. `REVIEW-TASK-0033-A`：`locked`
3. `REVIEW-TASK-0033-B`：`pending_token`
