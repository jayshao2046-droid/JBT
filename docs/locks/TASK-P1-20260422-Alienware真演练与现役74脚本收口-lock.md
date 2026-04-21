# TASK-P1-20260422-Alienware真演练与现役74脚本收口-lock

【状态】已收口
【日期】2026-04-22
【执行】Atlas

## 本批冻结白名单

1. DEPLOY_MINUTE_KLINE_FIX.sh
2. governance/scripts/jbt_rsync_deploy.sh
3. governance/scripts/jbt_rsync_rollback.sh
4. services/data/src/researcher/scheduler.py

## 只读执行范围

1. governance/scripts/jbt_rsync_deploy.sh
2. governance/scripts/jbt_rsync_rollback.sh

## 本批说明

1. 真实 deploy/rollback 演练默认基于现有治理脚本执行，不以演练名义预先扩展脚本写权限。
2. 仓内 74 清理只处理仍会真实执行的脚本入口。
3. 若真实演练暴露治理脚本缺陷，必须中止本批并补充新预审，不得顺手扩白名单。
4. 2026-04-22 00:47~00:55 已补充预审：允许对 deploy/rollback 脚本修复 Windows 目标传输与研究员重启路径，但不扩展到其他治理脚本。
5. 2026-04-22 01:10 已补充冻结：允许对 `services/data/src/researcher/scheduler.py` 做单文件最小修复，仅限移除未完成的 `HealthMonitor` 接入；不允许顺势新增 `health_monitor.py`、扩到 notifier 或扩大到 `services/data/**` 其他文件。

## 收口结果

1. 实际修改严格限于以下 4 个白名单文件：
	- DEPLOY_MINUTE_KLINE_FIX.sh
	- governance/scripts/jbt_rsync_deploy.sh
	- governance/scripts/jbt_rsync_rollback.sh
	- services/data/src/researcher/scheduler.py
2. 真实 deploy 结果：`researcher` Windows 文件同步成功，计划任务启动成功，`8199 /health` 通过。
3. 真实 rollback 结果：首次因历史坏快照失败，经重新生成已知健康快照后再次 rollback 成功，`8199 /health` 通过。
4. 无白名单外写入，无历史文档批量替换，无 `.env` / `runtime` / `logs` 越界修改。

## 锁定结论

1. 本批服务级最小修复已完成，不再需要扩大到 `services/data/**` 其他文件。
2. 后续若 researcher 再次出现运行期问题，应另开新任务，不得复用本批白名单继续顺手修改。