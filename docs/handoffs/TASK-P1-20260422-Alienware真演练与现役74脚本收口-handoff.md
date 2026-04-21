# TASK-P1-20260422-Alienware真演练与现役74脚本收口-handoff

【状态】已完成
【日期】2026-04-22
【执行】Atlas

## 交付目标

1. 完成 Alienware `researcher` 的真实 deploy/rollback 演练。
2. 收口仍会真实执行的 Mini 旧 IP 脚本入口。

## 本批修改

1. `DEPLOY_MINUTE_KLINE_FIX.sh`
	- Mini 默认地址 `192.168.31.74` → `192.168.31.76`
2. `governance/scripts/jbt_rsync_deploy.sh`
	- researcher Windows 重启分支优先切到 `JBT_Researcher_Service` 计划任务
3. `governance/scripts/jbt_rsync_rollback.sh`
	- researcher Windows 回滚后的重启分支同样优先切到 `JBT_Researcher_Service`
4. `services/data/src/researcher/scheduler.py`
	- 回退未完成的 `HealthMonitor` 接入
	- 不新增 `health_monitor.py`
	- 不扩到 notifier 或其他 researcher 文件

## 验证结果

1. 本地校验通过：
	- `bash -n DEPLOY_MINUTE_KLINE_FIX.sh`
	- `bash -n governance/scripts/jbt_rsync_deploy.sh`
	- `bash -n governance/scripts/jbt_rsync_rollback.sh`
	- 编辑器诊断：`scheduler.py` `No errors found`
2. researcher 本地最小导入验证通过：`ResearcherScheduler` 不再因 `HealthMonitor` 缺失而导入失败。
3. 真实 deploy 成功：
	- Windows 文件同步完成
	- researcher 重启成功
	- `http://192.168.31.223:8199/health` 首次通过
4. 第一次 rollback 失败原因已定位：回滚快照来自修复前的坏状态。
5. 通过两次同版本 deploy 重新生成已知健康快照后，第二次真实 rollback 成功：
	- researcher 重启成功
	- `8199 /health` 首次通过

## 关键结论

1. 这次问题不需要进入 Windows 桌面手工处理；macOS 侧通过 SSH + `schtasks /Run /TN JBT_Researcher_Service` 可以完成 researcher 的稳定拉起。
2. 真正阻塞闭环的另一半根因是仓内 `scheduler.py` 存在一段未完成的健康监控接入，而不是额外的 Windows 权限缺口。
3. rollback 演练必须基于“已知健康”的快照；若历史快照已被坏状态污染，第一次 rollback 失败并不代表脚本逻辑回归。

## 向 Jay.S 汇报摘要

Alienware researcher 已完成真实 deploy/rollback 演练闭环。Windows 侧不需要进桌面手工起服务，现有计划任务可由 Mac 侧远程触发；仓内 researcher 还顺带修掉了一个单文件代码一致性问题。另一个独立子项 `DEPLOY_MINUTE_KLINE_FIX.sh` 也已从 `192.168.31.74` 收口到 `192.168.31.76`。