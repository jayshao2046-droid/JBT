# TASK-P1-20260422-Alienware-sim-trading真演练

【状态】已完成
【日期】2026-04-22
【发起】Jay.S
【执行】Atlas
【类型】治理脚本演练 / Windows 发布链验证

## 背景

1. 上一批已完成 Alienware `researcher` 的真实 deploy/rollback 演练闭环，Windows 计划任务路径已验证可用。
2. Jay.S 继续要求完成第 1 项后续动作：对 Alienware `sim-trading` 执行一次独立的真实 deploy/rollback 演练。
3. `sim-trading` 风险高于 `researcher`，因此必须与前一批分开建档、分开审核、分开留痕，不共用 researcher 任务单收口。

## 本批边界

1. 只对 Alienware `sim-trading` 执行一次真实 deploy/rollback 演练，验证当前 `windows_uvicorn` 路径是否可闭环。
2. 默认先执行现有治理脚本，不预设业务代码或治理脚本修改。
3. 若真实演练暴露根因明确落在治理脚本或 `sim-trading` 单服务代码，再另开补充预审，不得顺手扩大本批范围。

## 白名单

### 仓内写入白名单

1. ATLAS_PROMPT.md
2. governance/scripts/jbt_rsync_deploy.sh
3. governance/scripts/jbt_rsync_rollback.sh

### 允许执行但默认不开写权限的现役治理脚本

1. governance/scripts/jbt_rsync_deploy.sh
2. governance/scripts/jbt_rsync_rollback.sh

说明：本批默认只执行现有脚本；只有当真实演练暴露根因明确落在上述白名单文件时，才允许按补充预审进入写入。

## 只读基线（2026-04-22）

1. `http://192.168.31.223:8101/health` 当前返回 `{"status":"ok","service":"sim-trading"}`。
2. Alienware 远端存在 `C:/Users/17621/JBT/services/sim-trading/src/main.py`。
3. Alienware 远端同时存在：
   - `C:/Users/17621/JBT/services/sim-trading/.venv/Scripts/python.exe`
   - `C:/Users/17621/JBT/.venv/Scripts/python.exe`
4. 当前最小假设：`jbt_rsync_deploy.sh` 里的 `windows_uvicorn` 分支可直接完成 sim-trading 真实 deploy；廉价反证检查已完成，未发现 researcher 类似的先验坏路径。

## 明确排除

1. services/**
2. shared/**
3. .github/**
4. docker-compose*.yml
5. 任一真实 .env
6. runtime/**
7. logs/**
8. 历史 task/review/report/reference/handoff 中的批量口径修订
9. researcher / data / decision / backtest 的任何顺手修改

## 验收标准

1. `sim-trading` 完成一次非 dry-run 的真实 deploy。
2. deploy 后 `8101 /health` 通过，并写入 manifest。
3. 从刚生成的有效快照完成一次真实 rollback。
4. rollback 后 `8101 /health` 再次通过，并写入 rollback manifest。
5. 本批无白名单外写入。

## 实际完成

1. 首次真实 deploy 暴露两个脚本侧根因：
   - `services/sim-trading/参考文档/` 中的 macOS framework symlink 会触发 Windows `robocopy` `RC=8`。
   - 现有 `robocopy /MIR` 会删除 Alienware 远端仅有的启动资产，包括 `.venv`、`.env`、`start_sim_trading.ps1`、`watchdog_sim_trading.ps1` 等。
2. 只读复盘与远端对比已确认：sim-trading 的稳定后台入口不是直接 `Start-Process python`，而是既有计划任务 `JBT_SimTrading_Watchdog`；在恢复启动资产后，显式触发该任务可重新拉起 `8101 /health`。
3. 已在白名单内对 `governance/scripts/jbt_rsync_deploy.sh` 与 `governance/scripts/jbt_rsync_rollback.sh` 做最小收口：
   - sim-trading payload 继续排除 `参考文档/`
   - Windows 同步保留远端启动资产：`.venv`、`runtime`、`.env`、`start_*.ps1`、`stop_*.ps1`、`watchdog*.ps1`、`watchdog_sim.log`、`check_trading_day.py`、`manage_sim_trading.py`
   - `restart_windows_uvicorn_service()` 优先触发 `JBT_SimTrading_Watchdog`，其次才回退到 `start_sim_trading.ps1` / 通用 uvicorn 启动
4. 为修复先前 `robocopy /MIR` 已删掉的远端启动资产，已从已知健康快照 `sim-trading-20260422-013258` 一次性恢复缺失资产到 Alienware live 目录；该动作仅发生在远端运行态，不新增仓内白名单外写入。
5. 真实 deploy 已成功执行：最新有效快照为 `C:/Users/17621/jbt-governance/snapshots/sim-trading-20260422-020522`，`8101 /health` 在第 2 次尝试通过。
6. 真实 rollback 已成功执行：从上述有效快照回滚后，`8101 /health` 同样在第 2 次尝试通过，deploy/rollback 演练闭环完成。