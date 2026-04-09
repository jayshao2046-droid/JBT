# TASK-0032 data端 data_web 临时看板导入

## 文档信息

- 任务 ID：TASK-0032
- 文档类型：独立前端临时看板任务建档
- 签名：Atlas
- 建档时间：2026-04-09
- 设备：MacBook

---

## 一、任务目标

在 `services/data/data_web/**` 下建立独立的 data 端临时看板工程，基于仓内参考目录 `services/data/参考文件/V0 DATA  0409` 导入页面与组件结构，用作当前 data 侧临时看板与视觉验证载体。

---

## 二、任务归属

1. `TASK-0032` 为 data 单服务独立前端任务。
2. 本任务不得并入 `TASK-0031` 热修批次，也不得借其白名单继续写入。
3. 本任务只处理临时看板工程本体，不改 `services/dashboard/**`，不改现有 data API 业务代码，不改共享库与部署文件。

---

## 三、参考来源

当前冻结的参考目录：

1. `services/data/参考文件/V0 DATA  0409/app/**`
2. `services/data/参考文件/V0 DATA  0409/components/**`
3. `services/data/参考文件/V0 DATA  0409/hooks/**`
4. `services/data/参考文件/V0 DATA  0409/lib/**`
5. `services/data/参考文件/V0 DATA  0409/public/**`
6. `services/data/参考文件/V0 DATA  0409/styles/**`
7. `services/data/参考文件/V0 DATA  0409/package.json`
8. `services/data/参考文件/V0 DATA  0409/next.config.mjs`
9. `services/data/参考文件/V0 DATA  0409/postcss.config.mjs`
10. `services/data/参考文件/V0 DATA  0409/tailwind.config.ts`
11. `services/data/参考文件/V0 DATA  0409/tsconfig.json`

---

## 四、页面冻结范围

当前必须纳入导入规划的页面 / 视图包括：

1. Overview
2. Collectors
3. Data Explorer
4. News Feed
5. System Monitor
6. Settings
7. `app/agent-network`
8. `app/command-center`
9. `app/intelligence`
10. `app/operations`
11. `app/systems`

---

## 五、任务边界

### 本轮允许处理

1. `services/data/data_web/**` 前端临时工程。
2. 为导入该工程而需要的新建 Next.js 配置文件、页面文件、组件文件、静态资源文件。
3. 与导入范围直接相关的最小前端依赖声明。

### 本轮明确排除

1. `services/dashboard/**`
2. `services/data/src/**` 后端业务代码
3. `shared/**`
4. `docker-compose.dev.yml`
5. 任一 `.env.example` / 真实 `.env`
6. 任一跨服务引用改造
7. 后端接口联调与数据契约改造

---

## 六、执行与锁控

当前状态：`locked`

1. `lockctl` 文件级 Token 已签发、校验并锁回：`tok-99645975-84fc-4cda-9d72-88a76110f787`。
2. 显式文件 manifest 固定为 `docs/locks/TASK-0032-data_web-manifest.md`，共 97 个目标文件；参考目录中的 `JBT-data.txt` 未导入。
3. `services/data/data_web/**` 已完成 97 文件导入，且严格落在 manifest 范围内。

---

## 七、执行结果

1. 目标目录 `services/data/data_web/**` 已创建完成，实际源码文件数为 97，与 manifest 一致。
2. 编辑器侧诊断结果：`No errors found`。
3. 环境补充：已在目标目录执行 `pnpm install --frozen-lockfile`。
4. 构建结果：`pnpm build` 成功，Next.js 15.2.6 生成如下静态路由：
	- `/`
	- `/_not-found`
	- `/agent-network`
	- `/command-center`
	- `/intelligence`
	- `/operations`
	- `/systems`
5. 项目架构师终审结论：无阻断发现，`REVIEW-TASK-0032` 通过。
6. lockback 结果：`approved`，token 状态 `locked`。

---

## 八、当前结论

1. `TASK-0032` 已完成任务建档、manifest 冻结、Token 签发、97 文件导入、最小构建验证、终审与锁回。
2. 当前交付物定位为 data 端临时看板原型，不扩展到真实 data API 联调。
3. 后续若要继续把 `data_web` 转为正式工程，必须另起新任务处理接口联调与类型治理。