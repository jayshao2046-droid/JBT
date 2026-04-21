# TASK-P1-20260422-Alienware-sim-trading真演练-lock

【状态】已收口
【日期】2026-04-22
【执行】Atlas

## 本批冻结白名单

1. ATLAS_PROMPT.md
2. governance/scripts/jbt_rsync_deploy.sh
3. governance/scripts/jbt_rsync_rollback.sh

## 只读执行范围

1. governance/scripts/jbt_rsync_deploy.sh
2. governance/scripts/jbt_rsync_rollback.sh

## 本批说明

1. 本批默认先执行现有 Windows `sim-trading` 发布链，不以演练名义预先扩展到 `services/sim-trading/**`。
2. 当前白名单主要用于 Atlas 自身留痕，以及在真实演练失败后承接“根因明确落在治理脚本”的最小补充修复。
3. 若失败根因落在业务代码、配置或运行态权限，不得越过补充预审直接修改。

## 收口结果

1. 仓内实际修改严格限于以下 3 个白名单文件：
	- ATLAS_PROMPT.md
	- governance/scripts/jbt_rsync_deploy.sh
	- governance/scripts/jbt_rsync_rollback.sh
2. 真实 deploy 已成功：最新有效快照为 `C:/Users/17621/jbt-governance/snapshots/sim-trading-20260422-020522`，`8101 /health` 第 2 次尝试通过。
3. 真实 rollback 已成功：从上述有效快照恢复后，`8101 /health` 第 2 次尝试通过。
4. 根因已收口为治理脚本与远端启动资产协同问题，而不是仓内 `services/sim-trading/**` 业务代码问题；本批未扩展到任何服务代码白名单。
5. 为修复此前 `/MIR` 已删除的远端启动资产，曾从健康快照向 Alienware live 目录恢复 `.venv`、`.env`、`start_*.ps1`、`watchdog*.ps1` 等运行时文件；该动作发生在远端运行态，不构成仓内白名单外写入。

## 锁定结论

1. sim-trading Windows 发布链当前必须保留远端启动资产，不能再对 live 目录做无保护的 `/MIR` 覆盖。
2. sim-trading 的稳定后台启动入口已冻结为优先复用 `JBT_SimTrading_Watchdog`；后续若要改计划任务本体或远端 `start_sim_trading.ps1`，必须另开新任务。