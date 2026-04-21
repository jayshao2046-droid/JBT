# REVIEW-TASK-P1-20260422-Alienware真演练与现役74脚本收口

【状态】已完成
【日期】2026-04-22
【审核】Atlas

## 预审结论

通过，允许按最小范围执行本批两个串行子项。

## 预审裁定

1. 真实演练优先使用 `researcher`，因为其当前健康、监听正常，且风险低于 `sim-trading`。
2. 本批默认不修改 `governance/scripts/jbt_rsync_deploy.sh` 与 `governance/scripts/jbt_rsync_rollback.sh`；先验证现有脚本是否已能真实闭环。
3. `192.168.31.74` 的仓内残留只处理“仍会真实执行”的脚本入口，不纳入历史文档、测试或注释型口径清理。
4. `services/data/scripts/disable_legacy.sh` 中旧 IP 仅位于注释与示例命令，不影响脚本运行逻辑，本批排除。

## 白名单

1. DEPLOY_MINUTE_KLINE_FIX.sh
2. governance/scripts/jbt_rsync_deploy.sh
3. governance/scripts/jbt_rsync_rollback.sh
4. services/data/src/researcher/scheduler.py

## 补充预审（2026-04-22 00:47）

1. 第一次 `researcher` 真实 deploy 已完成只读验证，失败日志先明确显示 Alienware 目标机不存在 `rsync`，随后重跑又确认研究员 Windows 重启逻辑未覆盖仓库根 `.venv` 路径。
2. 允许按最小范围修复 deploy/rollback 两脚本中的 Windows 传输与研究员重启路径，不扩展到其他治理文件。
3. 修复后必须优先重跑同一条 `researcher` 真实 deploy 校验，并完成真实 rollback 闭环；若仍失败，再决定是否另开补充预审。

## 补充预审（2026-04-22 01:10）

1. 继续只读排查后确认，当前 `researcher` 发布失败还叠加了仓内代码不一致问题：`services/data/src/researcher/scheduler.py` 引入了 `HealthMonitor`，但工作区内不存在 `services/data/src/researcher/health_monitor.py`；同一段初始化还引用了 `self.notifier.feishu_alert_webhook`，而当前 notifier 实现没有该属性。
2. 为保持最小修复面，不新增 `health_monitor.py`，也不扩展到 notifier、多文件联动或 `services/data/**` 批量修整；仅允许修改 `services/data/src/researcher/scheduler.py`，回退这段未完成的健康监控接入，使 researcher 恢复到可部署、可启动状态。
3. 该补充预审不改变本批服务边界，仍只限 `data/researcher` 单文件修复；完成后必须重新执行 `researcher` 非 dry-run deploy，并验证 `8199 /health`，然后再执行 rollback。

## 验收要求

1. `researcher` 真实 deploy 成功并通过 `8199 /health`。
2. `researcher` 真实 rollback 成功并再次通过 `8199 /health`。
3. `DEPLOY_MINUTE_KLINE_FIX.sh` 收口后不再指向 `192.168.31.74`。
4. 不夹带历史文档批量替换。

## 复核结果

通过。

### 复核证据

1. `bash -n DEPLOY_MINUTE_KLINE_FIX.sh` 通过，脚本内 `MINI_IP="192.168.31.76"` 已生效。
2. `bash -n governance/scripts/jbt_rsync_deploy.sh` 与 `bash -n governance/scripts/jbt_rsync_rollback.sh` 通过。
3. `services/data/src/researcher/scheduler.py` 单文件修复后，本地最小导入检查通过，编辑器诊断为 `No errors found`。
4. `bash governance/scripts/jbt_rsync_deploy.sh --service researcher` 非 dry-run 真实执行成功，Windows 文件同步完成，`8199 /health` 首次通过。
5. 第一次 rollback 失败已定位为回滚快照来自修复前的坏状态，不属于 rollback 代码回归。
6. 两次同版本 deploy 后重新生成已知健康快照，再执行 `bash governance/scripts/jbt_rsync_rollback.sh --service researcher`，`8199 /health` 首次通过，真实 rollback 闭环成功。

### 复核结论

1. Alienware researcher 的真实 deploy/rollback 演练已完成闭环。
2. Windows 远端不需要进入桌面手工起服务；通过 SSH 触发既有计划任务即可稳定收口。
3. 本批新增的 researcher 服务代码修复严格限于 `scheduler.py` 单文件，未扩展到其他 `services/data/**` 文件。