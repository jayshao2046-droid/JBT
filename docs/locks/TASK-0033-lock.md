# TASK-0033 Lock 记录

## Lock 信息

- 任务 ID：TASK-0033
- 当前总状态：`a_locked_b_active`
- 执行 Agent：数据

## 批次状态

### A 批：8105 数据面只读接口收口

1. review_id：`REVIEW-TASK-0033-A`
2. token_id：`tok-836bb68d-91b7-460d-ad28-f2905aa7b7dd`
3. 白名单：
	- `services/data/src/main.py`
	- `services/data/tests/test_main.py`
4. 当前状态：`locked`
5. lockback：`approved`
6. review_id：`REVIEW-TASK-0033-A`
7. lockback_summary：`TASK-0033 A 完成 4 个只读 dashboard 聚合接口与回归测试，终审通过，执行锁回`
8. 替换 token `tok-8a8394e5` 也已完成 lockback（3-day 补签，同范围），review-id `REVIEW-TASK-0033-A`，当前状态 `locked`

### B 批：3004 前端正式化与独立前端容器

1. review_id：`REVIEW-TASK-0033-B`
2. token_id：`tok-f4bdc258-2e5b-4554-b1b1-7ddc7bdd16e2`
3. 白名单：
	- `services/data/data_web/app/page.tsx`
	- `services/data/data_web/components/pages/overview-page.tsx`
	- `services/data/data_web/components/pages/collectors-page.tsx`
	- `services/data/data_web/components/pages/data-explorer-page.tsx`
	- `services/data/data_web/components/pages/news-feed-page.tsx`
	- `services/data/data_web/components/pages/system-monitor-page.tsx`
	- `services/data/data_web/components/pages/settings-page.tsx`
	- `services/data/data_web/next.config.mjs`
	- `services/data/data_web/package.json`
	- `services/data/data_web/Dockerfile`
4. 当前状态：`active`（3-day token，剩余 ~71h）

## 排除项

1. `shared/contracts/**`
2. `docker-compose.dev.yml`
3. 任一 `.env.example` / 真实 `.env`
4. 任一非 data 服务目录
5. 五个跨域原型页与参考素材目录
