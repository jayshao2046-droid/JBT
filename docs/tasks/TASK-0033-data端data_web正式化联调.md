# TASK-0033 data端 data_web 正式化联调

## 文档信息

- 任务 ID：TASK-0033
- 文档类型：data 单服务正式化联调任务建档
- 签名：Atlas
- 建档时间：2026-04-09
- 设备：MacBook

---

## 一、任务目标

在保持 data 单服务边界不变的前提下，把当前 `services/data/data_web/**` 从临时视觉原型升级为可验收的正式联调前端：六个 data 视图去掉 mock 主数据源，改为接入真实 data API，并在 Mini 上以独立前端容器方式按固定端口 `3004` 拉起供验收。

---

## 二、任务归属

1. `TASK-0033` 为 data 单服务正式化任务，不并入 `TASK-0032`。
2. 本任务只允许修改 `services/data/**` 与协同账本，不得扩展到其他服务。
3. 本任务不得触碰 `shared/contracts/**`、`docker-compose.dev.yml`、任一 `.env.example`、任一真实 `.env`。

---

## 三、范围冻结

### 本轮纳入正式化的 data 视图

1. Overview
2. Collectors
3. Data Explorer
4. News Feed
5. System Monitor
6. Settings

### 本轮从导航与验收范围移出的跨域原型页

1. `app/agent-network`
2. `app/command-center`
3. `app/intelligence`
4. `app/operations`
5. `app/systems`

---

## 四、执行批次

### 批次 A：8105 数据面只读接口收口

目标：

1. 在 data 单服务内补齐六个 data 视图所需的只读聚合接口。
2. 所有新增接口只能读取 data 服务本地数据、状态、进程与日志摘要，不得调用其他服务 API。
3. 同步补齐 `test_main.py` 最小回归，保证既有 `health`、`version`、`symbols`、`bars` 不回退。

白名单：

1. `services/data/src/main.py`
2. `services/data/tests/test_main.py`

状态：`pending_token`

实施结果：

1. 已新增 4 个只读聚合接口：`/api/v1/dashboard/system`、`/api/v1/dashboard/collectors`、`/api/v1/dashboard/storage`、`/api/v1/dashboard/news`。
2. 已补齐 `services/data/tests/test_main.py` 对 4 个聚合接口的最小回归，并补充绝对路径 / URL / IP 不外露的安全断言。
3. 本地验证结果：`get_errors = 0`；`pytest services/data/tests/test_main.py -q` = `6 passed`。
4. 项目架构师第三次只读终审结论：无阻断发现，可进入 lockback。
5. A 批 lockback 已完成：token_id=`tok-836bb68d-91b7-460d-ad28-f2905aa7b7dd`，review_id=`REVIEW-TASK-0033-A`，状态=`locked`。

### 批次 B：3004 前端正式化与独立前端容器

目标：

1. 六个 data 视图全部改接真实 API，不再以 mock 常量作为主数据源。
2. 主导航只保留六个 data 视图，跨域原型页移出本轮演示口径。
3. 允许新增 data_web 独立前端容器文件，在 Mini 上以 `3004` 拉起，不修改根编排。

白名单：

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

---

## 五、明确排除

1. `shared/contracts/**`
2. `docker-compose.dev.yml`
3. 所有环境样例文件与真实环境文件
4. 所有非 data 服务目录
5. `services/data/data_web/app/agent-network/page.tsx`
6. `services/data/data_web/app/command-center/page.tsx`
7. `services/data/data_web/app/intelligence/page.tsx`
8. `services/data/data_web/app/operations/page.tsx`
9. `services/data/data_web/app/systems/page.tsx`
10. data 参考素材与临时样板目录

---

## 六、验收标准

1. 8105 侧新增接口全部留在 data 单服务内，不新增跨服务依赖。
2. `services/data/tests/test_main.py` 对新增接口有稳定回归，且既有最小供数能力不退化。
3. 六个 data 视图全部展示真实数据或明确空态 / 异常态，不再使用 mock 常量作为主数据源。
4. 主导航只保留六个 data 视图，本轮不演示跨域原型页。
5. Collectors、Settings 等页面若缺少安全的写接口支撑，本轮必须保持只读、禁用或隐藏，不把本任务扩写成在线运维系统。
6. 端口保持 `data API = 8105`、`data-web = 3004`，根编排与环境文件零改动。
7. Git 提交完成后，代码需推送到 `local/main` 与 `origin/main`，并同步 Mini。
8. Mini 上需以独立 data_web 前端容器方式拉起 `3004`，并稳定访问本机 `8105`。

---

## 七、当前状态

1. Jay.S 已确认按推荐口径执行 `TASK-0033`。
2. 项目架构师只读预审结论：可继续，但建议按 A / B 两批执行。
3. A 批已完成实施、自校验、第三次终审与 lockback；当前 `services/data/src/main.py`、`services/data/tests/test_main.py` 已重新锁回。
4. B 批仍处于 `pending_token`，未签发前不得写入 `services/data/data_web/**` 白名单业务文件。
