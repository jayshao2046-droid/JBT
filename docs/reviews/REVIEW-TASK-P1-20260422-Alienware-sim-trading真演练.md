# REVIEW-TASK-P1-20260422-Alienware-sim-trading真演练

【状态】已完成
【日期】2026-04-22
【审核】Atlas

## 预审结论

通过，允许按最小范围执行 Alienware `sim-trading` 的真实 deploy/rollback 演练。

## 预审裁定

1. researcher 批次已闭环，本批必须独立建档，不与 researcher 共用 lockback 与 handoff。
2. 当前只读基线表明 sim-trading 具备直接演练条件：`8101 /health` 正常、远端 `src/main.py` 存在、服务目录与仓库根 `.venv` 均存在。
3. 因为 `windows_uvicorn` 分支尚未做过真实演练，本批默认先执行、不先修改；若 deploy/rollback 失败，再根据实际根因决定是否补充预审。
4. 本批不预开 `services/sim-trading/**` 白名单，不得以“顺手修启动”为由直接进入业务代码修改。

## 白名单

1. ATLAS_PROMPT.md
2. governance/scripts/jbt_rsync_deploy.sh
3. governance/scripts/jbt_rsync_rollback.sh

## 验收要求

1. `sim-trading` 真实 deploy 成功并通过 `8101 /health`。
2. `sim-trading` 真实 rollback 成功并再次通过 `8101 /health`。
3. 若真实演练失败，必须先写清根因落点，再决定是否补充预审。

## 复核结果

通过。

### 复核证据

1. 只读定位已确认首个同步根因：`services/sim-trading/参考文档/` 中的 macOS symlink 会导致 Windows `robocopy` `RC=8`；相关 payload 排除后，Windows 文件同步恢复成功。
2. 远端 live 目录与健康快照对比已确认第二个根因：原有 `robocopy /MIR` 会删除 sim-trading 远端独有启动资产（`.venv`、`.env`、`start_sim_trading.ps1`、`watchdog_sim_trading.ps1` 等），导致后续后台启动链失效。
3. 远端最小实验已验证：
	- 恢复启动资产后，前台运行 `start_sim_trading.ps1` 可稳定通过 `8101 /health`
	- 停掉 8101 后，显式触发 `JBT_SimTrading_Watchdog` 可重新恢复 `8101 /health`
4. `bash -n governance/scripts/jbt_rsync_deploy.sh` 与 `bash -n governance/scripts/jbt_rsync_rollback.sh` 均通过。
5. `bash governance/scripts/jbt_rsync_deploy.sh --service sim-trading` 非 dry-run 真实执行成功：
	- Windows 文件同步完成
	- `JBT_SimTrading_Watchdog` 启动路径生效
	- 最新有效快照：`sim-trading-20260422-020522`
	- `8101 /health` 第 2 次尝试通过
6. `printf 'y\n' | bash governance/scripts/jbt_rsync_rollback.sh --service sim-trading` 真实执行成功：
	- 有效快照恢复完成
	- 回滚后重启成功
	- `8101 /health` 第 2 次尝试通过

### 复核结论

1. sim-trading 的真实 deploy/rollback 演练已闭环。
2. 该服务在 Alienware 上的稳定后台入口应优先复用现有 `JBT_SimTrading_Watchdog`，而不是仓内脚本直接后台拉 `python -m uvicorn`。
3. Windows `robocopy /MIR` 不能再无保护地覆盖 sim-trading 远端目录，否则会删除远端启动资产并破坏发布链。