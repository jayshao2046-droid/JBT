# TASK-0033 data_web 正式化联调交接单

【签名】Atlas
【时间】2026-04-09 21:12
【设备】MacBook

## 一、交接目标

完成 `TASK-0033` 的独立建档，并完成 A 批 `8105` 只读聚合接口收口、验证、终审与锁回。

## 二、当前结论

1. Jay.S 已确认采用推荐方案，`TASK-0033` 继续按 A / B 两批执行。
2. A 批已完成：`services/data/src/main.py` / `services/data/tests/test_main.py` 内新增 4 个只读聚合接口，并已补齐回归测试。
3. A 批验证结果：`get_errors = 0`；`pytest services/data/tests/test_main.py -q` = `6 passed`。
4. 项目架构师第三次只读终审结论：无阻断发现，可进入 lockback；A 批 token `tok-836bb68d-91b7-460d-ad28-f2905aa7b7dd` 已按 `REVIEW-TASK-0033-A` 成功锁回，状态 `locked`。
5. 当前整体边界保持不变：data 单服务内六个 data 视图做真联调，五个跨域原型页移出导航与验收范围；根编排、共享契约、环境文件、非 data 服务目录继续排除。

## 三、下一步

1. 下一步只允许签发 B 批 Token，范围严格限于六个 data 页面、`app/page.tsx`、`next.config.mjs`、`package.json` 与 `data_web/Dockerfile`。
2. B 批实施时继续保持只读前端口径，不把 Collectors / Settings 扩写成在线运维系统。
3. B 批完成后，执行本地构建、git 提交推送、Mini 同步、远端容器拉起、终审与 lockback。
