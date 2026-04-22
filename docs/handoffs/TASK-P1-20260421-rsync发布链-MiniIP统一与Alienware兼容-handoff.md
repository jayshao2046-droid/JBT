# TASK-P1-20260421-rsync发布链-MiniIP统一与Alienware兼容-handoff

【状态】已完成
【日期】2026-04-21
【执行】Atlas

## 交接目标

1. 修正现役 rsync 发布链中的 Mini 地址口径（74 → 76）。
2. 补齐 Alienware Windows 分支，避免继续套用 Unix 重启模型。
3. 只验证治理脚本本身，不扩展到服务代码发布。

## 修改摘要

1. `governance/scripts/jbt_rsync_deploy.sh`
	- Mini 默认地址 `192.168.31.74` → `192.168.31.76`
	- 新增 `sim-trading` / `researcher` 服务发布入口
	- 新增 Alienware Windows 快照、重启、健康检查分支
	- 新增 manifest 字段：`ip`、`remote_dest`
2. `governance/scripts/jbt_rsync_rollback.sh`
	- Mini 默认地址 `192.168.31.74` → `192.168.31.76`
	- 新增 `sim-trading` / `researcher` 服务回滚入口
	- 新增 Windows 快照存在性检查、恢复、重启分支
	- 兼容读取新 manifest 字段

## 验证结果

1. `bash -n governance/scripts/jbt_rsync_deploy.sh` 通过。
2. `bash -n governance/scripts/jbt_rsync_rollback.sh` 通过。
3. deploy dry-run 验证通过：
	- `--service data` 指向 Mini `192.168.31.76`
	- `--service sim-trading` 指向 Alienware Windows 路径
	- `--service researcher` 指向 Alienware Windows 路径
4. Alienware 远端只读验证通过：
	- `C:/Users/17621/JBT/services/data`
	- `C:/Users/17621/JBT/services/sim-trading`
	均可通过 `powershell -EncodedCommand` 正常访问。

## 残留风险

1. 本批没有批量修改历史 task/review/report 中的旧 `192.168.31.74` 文案；历史材料仍会保留旧口径。
2. Windows 重启分支基于当前 Alienware 现网目录结构；若远端后续更换启动脚本名或 Python 路径，需要再做一次针对性收口。

## 向 Jay.S 汇报摘要

rsync 发布链现役入口已收口：Mini 默认目标统一为 `192.168.31.76`，Alienware 已补齐 Windows 发布/回滚分支，`sim-trading` 和 `researcher` 两条线都能进入同一套 git-free 交付链。历史审计文档没有批量清洗，保留原始事实。

## 下一步建议

1. 若要继续清理仓库内的旧 `192.168.31.74` 文案，建议单独建一条“历史文档口径统一”任务，不混在现役脚本修复里。
2. 若要验证 Windows 分支的真实发布，可先用 `sim-trading` 做一次 `--skip-health` 的小流量演练，再补一次正式健康检查。