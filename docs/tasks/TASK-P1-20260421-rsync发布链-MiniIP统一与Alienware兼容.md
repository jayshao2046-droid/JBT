# TASK-P1-20260421-rsync发布链-MiniIP统一与Alienware兼容

【状态】已完成
【日期】2026-04-21
【发起】Jay.S
【执行】Atlas
【类型】治理脚本收口 / 部署链修复

## 背景

1. 当前现役 rsync 发布链脚本仍把 Mini 地址写为 192.168.31.74；实测 192.168.31.74 超时，192.168.31.74 SSH 可达且 data 容器健康。
2. 现役 rsync 发布链仅覆盖 Unix 端重启模型；Alienware 为 Windows 节点，不能继续复用 docker restart / nohup 分支。
3. Jay.S 当前指令：全部改成 76，并继续完成 Alienware Windows 兼容处理。

## 本批边界

仅允许修改以下 2 个治理脚本：

1. governance/scripts/jbt_rsync_deploy.sh
2. governance/scripts/jbt_rsync_rollback.sh

明确不纳入：

1. services/**
2. shared/**
3. .github/**
4. docker-compose*.yml
5. 任一真实 .env
6. 历史审计 / 历史报告中保留事实口径的旧 IP 批量替换

## 目标

1. 将现役 rsync 发布链中的 Mini 地址统一到 192.168.31.74。
2. 为 Alienware 增加独立 Windows 分支，不再假设远端是 Unix + Docker。
3. 保持 dry-run 为纯离线预演，不依赖远端网络。
4. 对 sim-trading / researcher 这两个 Alienware 现网服务给出可执行的发布/回滚路径。

## 验收标准

1. deploy / rollback 两脚本 bash 语法通过。
2. `--service sim-trading --dry-run` 与 `--service researcher --dry-run` 可离线执行。
3. Mini 默认目标不再使用 192.168.31.74。
4. Alienware 分支具备 Windows 快照、重启和健康检查逻辑。

## 实际完成

1. `governance/scripts/jbt_rsync_deploy.sh` 已将 Mini 默认地址统一为 `192.168.31.74`。
2. 发布链新增 `sim-trading` 与 `researcher` 两个 Alienware 服务入口。
3. Alienware 分支已切换为 Windows 快照 / 重启模型，并通过 `EncodedCommand` 解决 SSH + PowerShell 引号吞变量问题。
4. `governance/scripts/jbt_rsync_rollback.sh` 已同步补齐 Windows 路径恢复与重启逻辑。
5. `install_jbt_service_guardian.sh` 与 `jbt_service_guardian.py` 未改动：现状只读核对确认 guardian 里的 Mini `76` 和 Alienware `223` 已正确。