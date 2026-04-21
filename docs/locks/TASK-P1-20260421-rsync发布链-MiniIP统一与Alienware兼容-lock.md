# TASK-P1-20260421-rsync发布链-MiniIP统一与Alienware兼容-lock

【状态】已收口
【日期】2026-04-21
【执行】Atlas

## 本批冻结白名单

1. governance/scripts/jbt_rsync_deploy.sh
2. governance/scripts/jbt_rsync_rollback.sh

## 本批说明

1. 本批为治理脚本最小收口，不触及 `services/**`、`shared/**`、`.github/**`、`docker-compose*.yml`、真实 `.env`。
2. Mini 旧地址 192.168.31.74 已确认不可达；192.168.31.76 为当前可达地址。
3. Alienware 作为 Windows 节点，必须由脚本显式处理 Windows 快照 / 重启逻辑。

## 待补内容

1. 验证结果已补齐。
2. 本批白名单之外无新增写入。

## 收口结果

1. 实际修改文件仍严格限于：
	- governance/scripts/jbt_rsync_deploy.sh
	- governance/scripts/jbt_rsync_rollback.sh
2. 验证结果：bash 语法通过；3 个 dry-run 场景通过；Alienware `EncodedCommand` 只读验证通过。
3. 未触及 `services/**`、`shared/**`、`.github/**`、`docker-compose*.yml`、真实 `.env`。