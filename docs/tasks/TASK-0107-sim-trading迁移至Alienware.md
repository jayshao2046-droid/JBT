# TASK-0107：sim-trading 服务迁移至 Alienware（裸 Python 落地，Docker 化后置）

## 任务信息

- 任务 ID：TASK-0107
- 任务名称：sim-trading 迁移至 Alienware（裸 Python 落地，Docker 化后置）
- 所属服务：sim-trading
- 执行 Agent：模拟交易 Agent（Copilot）
- 前置依赖：TASK-0041 / TASK-0042（sim-trading v1.0.0 已完成 Mini 收口）
- 允许修改文件白名单：
  - `services/sim-trading/`（本地只读参考，不修改）
  - Alienware 远端同步：src/, configs/, requirements.txt（只读复制，不修改源）
  - Alienware 远端配置：`.env`、Python 启动脚本、schtasks 定时任务
- 是否需要 Token：是（远端部署无锁控文件，但遵守治理流程）
- 计划验证方式：`curl http://192.168.31.187:8101/health` 返回 200，CTP 连接状态确认
- 当前状态：✅ 已完成并锁回（`tok-6c984fae-f518-4fdc-82c8-772e0601e598` approved，2026-04-15）

## 任务目标

将 Mini 上已完成治理收口的 sim-trading 运行面正式迁移到 Alienware（Windows x86_64），用于：
1. 提供稳定的 Windows 本地运行环境，承载 CTP 开盘连通测试与交易执行。
2. 将 Mini 职责收窄为纯数据采集节点，统一四设备运行架构口径。

**执行结果说明**：实际交付形态为 Alienware 裸 Python 运行，不是 Docker 容器。Docker 化部署因 BIOS 虚拟化未开启而后置，不阻塞本次迁移收口。

## 实际交付结果

| 项目 | Mini | Alienware |
|------|------|-----------|
| OS | macOS ARM64 | Windows x86_64 |
| 运行形态 | Docker | 裸 Python |
| 平台 | `linux/arm64` | `windows/x86_64` |
| CTP 前置 | 7x24 SimNow | 光大期货（同一批地址） |
| 服务端口 | 8101 | 8101 |

## 执行记录

- [x] Alienware Python 3.11 运行环境建立
- [x] `openctp-ctp 6.7.11` 与依赖安装完成
- [x] src/, configs/, requirements.txt 同步到 Alienware
- [x] `.env`（CTP 凭证）配置完成
- [x] 裸 Python 启动服务成功
- [x] `/health` 接口验证通过（HTTP 200）
- [x] 运行态确认：`stage=1.0.0`、`trading_enabled=true`、`active_preset=sim_50w`
- [x] schtasks 六组定时任务（早/午/夜开停）建立完成
- [x] Token lockback 完成（approved）

## 交付标准

1. `curl http://192.168.31.187:8101/health` 返回 `{"status":"ok"}`
2. MacBook 可通过内网 IP 访问 Alienware 8101 端口
3. Alienware 已成为正式 sim-trading 承载面；Mini 不再承载 sim-trading
4. 后续 Docker 化部署单独建任务推进，不影响当前验收成立
