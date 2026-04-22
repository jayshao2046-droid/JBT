# LOCK-TASK-0036 data端 U0 外盘分钟K线 0产出修复

## 文档信息

- 任务 ID：TASK-0036
- 锁回类型：U0 事后锁回
- 执行人：Atlas
- 锁回时间：2026-04-10 13:15
- 设备：MacBook

---

## 锁定文件清单

| 文件路径 | 状态 | 关联提交 |
|---------|------|---------|
| `services/data/src/collectors/overseas_minute_collector.py` | 已锁回 | `300c77d` |
| `services/data/src/scheduler/pipeline.py` | 已锁回 | `300c77d` |

---

## 锁回摘要

- Git 提交：`300c77d` — `fix(data-overseas): U0热修 - 外盘分钟K线 0产出修复`
- 推送至：`origin main`（GitHub）
- 两地同步：MacBook（本地）+ Mini `jaybot@172.16.0.49:~/JBT/`（蒲公英）
- 审查通过：`REVIEW-TASK-0036` PASS

---

## 后继约束

1. 上述两文件本轮已锁回，下次修改须重新走标准流程或新一轮 U0 指令。
2. `CT=F` / `RS=F` 两个 ticker 问题属已知限制，若需补齐备源须另起任务。
3. `TASK-0034`/`TASK-0035` 等既有锁回不受本次影响。
