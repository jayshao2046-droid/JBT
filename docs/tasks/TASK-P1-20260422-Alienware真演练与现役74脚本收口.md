# TASK-P1-20260422-Alienware真演练与现役74脚本收口

【状态】已完成
【日期】2026-04-22
【发起】Jay.S
【执行】Atlas
【类型】治理脚本演练 / 现役脚本口径收口

## 背景

1. 上一批已完成 rsync 发布链对 Mini `192.168.31.76` 与 Alienware Windows 分支的脚本兼容收口，但还缺一次真实 deploy/rollback 闭环演练。
2. 仓库内仍有少量 `192.168.31.74` 残留；其中真正会影响执行的现役脚本已收敛到根目录 `DEPLOY_MINUTE_KLINE_FIX.sh`。
3. `services/data/scripts/disable_legacy.sh` 等命中仅在注释/示例中出现旧 IP，不进入脚本实际执行逻辑，本批不纳入修改。

## 本批边界

本批按两个串行子项收口：

1. 对 Alienware `researcher` 执行一次真实 deploy/rollback 演练，验证现有治理脚本闭环。
2. 只清理仍会真实执行的旧 IP 脚本，不做历史文档与测试口径批量替换。

## 白名单

### 仓内写入白名单

1. DEPLOY_MINUTE_KLINE_FIX.sh
2. governance/scripts/jbt_rsync_deploy.sh
3. governance/scripts/jbt_rsync_rollback.sh
4. services/data/src/researcher/scheduler.py

### 允许执行但默认不开写权限的现役治理脚本

1. governance/scripts/jbt_rsync_deploy.sh
2. governance/scripts/jbt_rsync_rollback.sh

说明：只有当真实演练暴露根因明确落在上述治理脚本本身时，才允许另开补充预审，不在本批默认写入范围内。

补充说明（2026-04-22 00:47~00:55）：第一次 `researcher` 真实 deploy 已执行，先暴露 Windows 传输路径仍误用 `rsync`，后续重跑又暴露 Windows 研究员重启逻辑漏掉仓库根 `.venv` 相对路径。由于 deploy 与 rollback 两脚本共用同一类 Windows 重启逻辑，因此本批按最小范围一并纳入修复，仍不扩展到其他目录。

补充说明（2026-04-22 01:10~01:27）：继续只读排查后确认，当前 `researcher` 真实 deploy 未闭环不再只是 Windows 启动方式问题，仓内 `services/data/src/researcher/scheduler.py` 自身还包含一段未完成的健康监控接入：文件引用 `from .health_monitor import HealthMonitor`，但目录内不存在对应模块，同时还读取 `self.notifier.feishu_alert_webhook` 这一当前 notifier 中不存在的属性。为避免扩大到新增模块或多文件并修，本批补充最小服务代码修复范围，仅允许回退 `scheduler.py` 中这段未完成接入，使其恢复到可部署状态。

## 明确排除

1. services/**
2. shared/**
3. .github/**
4. docker-compose*.yml
5. 任一真实 .env
6. runtime/**
7. logs/**
8. 历史 task/review/report/reference/handoff 中保留事实口径的旧 IP 批量清洗
9. 仅在注释/示例命令中出现 74 且不影响执行逻辑的脚本
10. `services/data/src/researcher/` 下除 `scheduler.py` 外的其他文件

## 验收标准

1. `researcher` 完成一次非 dry-run 的真实 deploy。
2. deploy 后 `8199` 健康检查通过，并写入 manifest。
3. 从刚生成的有效快照完成一次真实 rollback。
4. rollback 后 `8199` 健康检查再次通过，并写入 rollback manifest。
5. `DEPLOY_MINUTE_KLINE_FIX.sh` 不再把 Mini 默认目标指向 `192.168.31.74`。
6. 本批无白名单外写入。

## 实际完成

1. `DEPLOY_MINUTE_KLINE_FIX.sh` 已将 Mini 默认目标从 `192.168.31.74` 收口到 `192.168.31.76`，本地 `bash -n` 通过。
2. `governance/scripts/jbt_rsync_deploy.sh` 与 `governance/scripts/jbt_rsync_rollback.sh` 已将 `researcher` 的 Windows 重启路径优先切到既有 `JBT_Researcher_Service` 计划任务，避免继续依赖 SSH 会话内直接后台拉起 Python 进程。
3. `services/data/src/researcher/scheduler.py` 已完成单文件最小修复：移除未完成的 `HealthMonitor` 接入，不新增 `health_monitor.py`，不扩展到 notifier 或其他 researcher 文件；本地导入与编辑器诊断均通过。
4. `researcher` 真实 deploy 已成功执行，`http://192.168.31.223:8199/health` 在首次尝试即通过。
5. 第一次真实 rollback 使用的是修复前污染状态生成的旧快照，健康检查失败；该现象已定位为“快照源无效”而非 rollback 脚本回归。
6. 随后通过两次同版本 deploy 重新生成“已知健康”的有效快照，并再次执行真实 rollback；`8199 /health` 在首次尝试即通过，deploy/rollback 演练闭环完成。
7. 本批所有关键文件本地校验通过：
	- `governance/scripts/jbt_rsync_deploy.sh`
	- `governance/scripts/jbt_rsync_rollback.sh`
	- `services/data/src/researcher/scheduler.py`
	- `DEPLOY_MINUTE_KLINE_FIX.sh`