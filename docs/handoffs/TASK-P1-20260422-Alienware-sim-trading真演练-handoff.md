# TASK-P1-20260422-Alienware-sim-trading真演练-handoff

【状态】已完成
【日期】2026-04-22
【执行】Atlas

## 交付目标

1. 完成 Alienware `sim-trading` 的真实 deploy/rollback 演练。
2. 在不扩展到 `services/sim-trading/**` 业务代码的前提下，收口当前 Windows 发布链。

## 本批修改

1. governance/scripts/jbt_rsync_deploy.sh
   - sim-trading payload 继续排除 `参考文档/`
   - Windows `robocopy /MIR` 同步改为保留远端启动资产：`.venv`、`runtime`、`.env`、`start_*.ps1`、`stop_*.ps1`、`watchdog*.ps1`、`watchdog_sim.log`、`check_trading_day.py`、`manage_sim_trading.py`
   - `restart_windows_uvicorn_service()` 优先触发 `JBT_SimTrading_Watchdog`
2. governance/scripts/jbt_rsync_rollback.sh
   - 与 deploy 侧保持同样的 sim-trading Windows 重启策略，优先复用 `JBT_SimTrading_Watchdog`
3. ATLAS_PROMPT.md
   - 已补记本批根因、修复路径与闭环结果

## 关键发现

1. `services/sim-trading/参考文档/` 含 macOS framework symlink，会导致 Windows `robocopy` 返回 `RC=8`；该目录不能进入 Windows payload。
2. 之前的 `robocopy /MIR` 会删除 Alienware live 目录内远端独有启动资产，这是 sim-trading 发布链失败的核心原因之一。
3. sim-trading 在 Alienware 上的稳定后台入口不是直接后台拉 `python -m uvicorn`，而是既有计划任务 `JBT_SimTrading_Watchdog`。
4. 为修复先前被删掉的启动资产，已从健康快照 `sim-trading-20260422-013258` 向 live 目录恢复 `.venv`、`.env`、`start_sim_trading.ps1`、`watchdog_sim_trading.ps1` 等远端运行时文件。

## 验证结果

1. `bash -n governance/scripts/jbt_rsync_deploy.sh` 通过。
2. `bash -n governance/scripts/jbt_rsync_rollback.sh` 通过。
3. 远端最小实验已验证：恢复启动资产后，前台运行 `start_sim_trading.ps1` 可通过 `8101 /health`。
4. 远端最小实验已验证：停掉 `8101` 后，触发 `JBT_SimTrading_Watchdog` 可恢复 `8101 /health`。
5. 真实 deploy 成功：
   - 最新有效快照：`C:/Users/17621/jbt-governance/snapshots/sim-trading-20260422-020522`
   - `8101 /health` 第 2 次尝试通过
6. 真实 rollback 成功：
   - 从上述有效快照恢复
   - `8101 /health` 第 2 次尝试通过

## 后续口径

1. 后续若继续用当前治理脚本发布 sim-trading，必须保留远端启动资产，不能再对 Alienware live 目录做无保护的 `/MIR` 覆盖。
2. 后续若要修改 `JBT_SimTrading_Watchdog` 计划任务本体或远端 `start_sim_trading.ps1`，必须另开新任务；本批不覆盖计划任务定义本身。
3. 若再次出现“端口短暂监听后退出”的现象，先检查 live 目录中的 `.venv` / `start_sim_trading.ps1` / `watchdog_sim_trading.ps1` 是否被误删，再检查计划任务是否仍存在。