# TASK-0028 预审记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0028 |
| 任务标题 | 数据端通知系统全量建设 |
| 预审类型 | 历史账本补档 + B6 补充批次预审 |
| 预审人 | 项目架构师 |
| 审核日期 | 2026-04-09 |

---

## 预审检查项

### 1. 服务归属

- [x] 归属明确：`services/data/**` 单服务
- [x] 不涉及跨服务 import
- [x] 不涉及 `shared/contracts/**` 变更

### 2. 历史账本补档

- [x] `TASK-0028` 主批次已实施并在任务单登记 13 个目标文件
- [x] 仓库当前缺失 `docs/reviews/TASK-0028-review.md` 与 `docs/locks/TASK-0028-lock.md`
- [x] 本次先补齐 review/lock 治理账本，再冻结补充批次 B6

### 3. B6 边界冻结

- [x] B6 继续归入 `TASK-0028`，不新建独立任务
- [x] 目标限定为通知体验优化，不承接采集链修复
- [x] 范围仅限 scheduler + notify + notify tests 四个文件

#### B6 白名单

1. `services/data/src/scheduler/data_scheduler.py`
2. `services/data/src/notify/dispatcher.py`
3. `services/data/src/notify/news_pusher.py`
4. `services/data/tests/test_notify.py`

#### B6 排除范围

1. `services/data/src/scheduler/pipeline.py`
2. `services/data/src/collectors/overseas_minute_collector.py`
3. `services/data/src/main.py`
4. `services/data/src/health/**`
5. `services/data/.env.example`
6. `shared/contracts/**`
7. `runtime/`、`logs/`、Mini 线上配置与真实密钥

### 4. 已知根因与边界裁决

- [x] 外盘分钟 0 产出根因已查明：`yfinance` 退避冷却叠加 `Alpha Vantage` / `Twelve Data` key 未配置
- [x] 本批仅调整通知语义与路由，不修复 backoff / fallback / API key 配置
- [x] 如需修改 `pipeline.py` 或 `collectors/overseas_minute_collector.py`，必须重新补审追加白名单

### 5. 验收标准

1. 同一调度时间窗内的完成类通知合并为单条摘要通知，不能继续逐采集器轰炸。
2. 同一时间新闻推送合并为单条摘要通知。
3. 新闻静默窗口调整为 22:00-08:30，P0 与显式 bypass 语义保持不变。
4. 单独采集允许单独推送，但仅飞书，不发邮件。
5. 外盘分钟 0 产出不得继续按“采集完成”成功通知处理，正文需显式区分“0 产出”与“成功完成”。
6. 自校验需覆盖同窗合并、新闻批量推送、0 产出路径、静默窗口边界四类场景。

### 6. 风险识别

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| TASK-0028 历史 review/lock 缺失 | 高 | 先补齐账本，再申请 B6 Token |
| 通知线 `flush` / `flush_batch` 接口口径不一致 | 中 | B6 自校验覆盖新闻批量路径 |
| 静默窗口若做全局修改，可能误伤非新闻通知 | 中 | 仅对新闻线延后到 08:30，不顺手扩大范围 |
| 借通知任务顺手修改 collector / pipeline | 高 | 明确排除并要求重新补审 |

---

## 预审结论

**通过**。`TASK-0028` 主批次 review/lock 账本需补齐；补充批次 `TASK-0028-B6` 可按 P1 范围申请单批次 Token。B6 仅允许修改四个白名单文件，不得扩展到采集链、运行态配置或跨服务路径。

---

## TASK-0028-B6 正式终审

- 审核阶段：批次 B6 正式终审
- 当前 active token_id：`tok-1e39e91a-191a-4b6f-afde-03dcc6f7b8c4`
- 审核时间：2026-04-09
- 审核结论：**未通过；不得 lockback**

### 1. 定向核验范围

1. 本次终审仅按 `TASK-0028-B6` 的 4 个白名单文件定向核验：
	- `services/data/src/scheduler/data_scheduler.py`
	- `services/data/src/notify/dispatcher.py`
	- `services/data/src/notify/news_pusher.py`
	- `services/data/tests/test_notify.py`
2. 当前定向 `git diff --name-only` 已复核，业务改动仍严格限于上述 4 个白名单文件；仓库中其他 dirty files 不纳入本批终审结论。

### 2. 已复核通过项

1. 4 个白名单文件 `get_errors = 0` 已复核。
2. 数据 Agent 提交的最小自校验 `pytest services/data/tests/test_notify.py -q` 当前结果为 `10 passed`，已纳入本次终审背景。
3. `services/data/src/notify/dispatcher.py` 中同窗采集摘要合并、NEWS `22:00-08:30` 静默窗口、以及采集摘要 `channels={"feishu"}` 的局部语义已经落地。
4. `services/data/src/notify/news_pusher.py` 已把 `flush` / `flush_batch` 收口为单条新闻摘要事件，`services/data/tests/test_notify.py` 也新增了同窗合并、0 产出、静默窗口边界与新闻摘要的最小单测覆盖。

### 3. 阻断点

1. **`services/data/src/scheduler/data_scheduler.py` 的 `job_news_push_batch()` 仍未把 storage -> `NewsPusher` 缓冲链路接通。**
	当前 scheduler 只执行 `pusher = NewsPusher()` 与 `pusher.flush()`；但 `services/data/src/notify/news_pusher.py` 中为此准备的 `sync_from_storage()` 并未在任何业务代码路径里被调用。与此同时，`services/data/src/scheduler/pipeline.py` 的 `run_news_api_pipeline()` / `run_rss_pipeline()` 仅把新闻写入 storage，不会写入 `NewsPusher` 的内存缓冲。结果是 B6 虽然把 `flush` / `flush_batch` 的事件模型收口为单条摘要，但 APScheduler 实际批量 job 仍拿不到待推送新闻，`news_pusher / scheduler` 断裂链路未闭环，验收目标“同一时间新闻推送合并为单条摘要通知”在真实调度路径上不成立。
2. **`services/data/src/scheduler/data_scheduler.py` 的 `job_news_push_batch()` 末尾残留未定义变量 `n`。**
	当前函数 `try/except` 结束后仍执行 `if n: n.reset_daily()`，但函数内部并未定义 `n`。这会在 job 执行路径上触发 `NameError`，使新闻批量推送任务无法稳定运行；在该运行时错误未消除前，本批不能视为“已完成终审可锁回”。

### 4. 终审结论

1. **`TASK-0028-B6` 正式终审未通过。**
2. **本批不得执行 lockback。**
3. **请数据 Agent 在现有 4 文件白名单内完成以下修复后重新回交终审：**
	- 在 `job_news_push_batch()` 中显式把 storage 新闻同步进 `NewsPusher`（例如走 `sync_from_storage()`）后再执行 `flush()`；
	- 删除或改正末尾未定义变量 `n` 的路径；
	- 补一条覆盖 scheduler -> storage -> `NewsPusher` 批量推送链路的最小回归测试，避免当前仅单测 `NewsPusher.flush()` 手工注入路径而遗漏真实调度入口。

---

## TASK-0028-B6 补丁后复审

- review-id：`REVIEW-TASK-0028-B6`
- 审核阶段：批次 B6 补丁后复审
- 审核时间：2026-04-09
- 审核结论：**通过；可 lockback**

### 1. 定向复核范围

1. 本次复审仍只核验 `TASK-0028-B6` 的 4 个白名单文件：
	- `services/data/src/scheduler/data_scheduler.py`
	- `services/data/src/notify/dispatcher.py`
	- `services/data/src/notify/news_pusher.py`
	- `services/data/tests/test_notify.py`
2. 定向 `git diff --name-only -- services/data` 已复核，当前数据端实际业务改动仍严格限于上述 4 个白名单文件。

### 2. 复核结果

1. `services/data/src/scheduler/data_scheduler.py` 的 `job_news_push_batch()` 当前已按正确顺序先执行 `pusher.sync_from_storage()`，再执行 `pusher.flush()`；此前 storage -> `NewsPusher` 缓冲链路未接通的阻断已消除。
2. 上轮残留的未定义变量 `n` 已不再出现在 `job_news_push_batch()` 中；`n.reset_daily()` 当前仅保留在 `job_daily_reset()` 的合法作用域，NameError 风险已消除。
3. `services/data/tests/test_notify.py` 已新增 scheduler 回归测试 `test_job_news_push_batch_syncs_storage_before_flush()`，覆盖真实调度入口“先 sync 再 flush”的顺序要求。
4. 4 个白名单文件 `get_errors = 0` 已复核。
5. 独立复跑 `PYTHONPATH=. ./.venv/bin/pytest services/data/tests/test_notify.py -q`，当前结果为 `11 passed`。

### 3. 复审结论

1. `TASK-0028-B6` 本轮补丁已消除上轮两个终审阻断点。
2. 本批当前满足既定验收标准。
3. **`REVIEW-TASK-0028-B6` 结论：通过，可 lockback。**

---

【签名】项目架构师
【时间】2026-04-09 09:05
【设备】MacBook