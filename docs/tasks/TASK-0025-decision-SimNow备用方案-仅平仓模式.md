# TASK-0025 — 决策端 SimNow 备用方案（仅平仓模式）

【签名】Atlas
【时间】2026-04-08
【设备】MacBook
【状态】✅ 已完成（Claude 执行 + Atlas 审核通过）
【Token】tok-e2c4419a-9f2f-4078-bae1-c5ca91a3c9c4（4320min / agent=claude）
【优先级】P1
【服务归属】services/decision/**

---

## 一、需求来源

Jay.S 于 TASK-0024 全平台部署就绪审查中提出：

> 决策端需要通过模拟交易端 `.env` 抓取 SimNow 凭证并登录。
> 目的是模拟交易端离线时，决策端启动备用方案。
> 备用模式仅可执行平仓，禁止开仓，直到模拟交易端恢复连接。

## 二、需求描述

### 场景

决策端正常通过 `sim_adapter.py` → `POST /api/v1/strategy/publish` 向模拟交易端发布策略执行指令。
当模拟交易端（Mini 容器 `JBT-SIM-TRADING-8101`）因网络断开、容器崩溃或维护停机等原因不可达时，
决策端需自动切换到 **SimNow 备用直连模式**，确保已有持仓可安全平仓。

### 功能定义

1. **连通性检测**：决策端定期（如 30s）探测模拟交易端 `/health` 是否响应
2. **备用模式触发**：连续 N 次探测失败后，自动进入备用模式
3. **SimNow 直连**：决策端读取模拟交易端 `.env` 或共享凭据，使用 CTP/TTS API 直接连接 SimNow
4. **仅平仓约束**：备用模式下只允许平仓操作，禁止新建仓位（开仓）
5. **模式恢复**：模拟交易端恢复连通后，自动退出备用模式，恢复正常发布链路
6. **通知**：进入/退出备用模式时发送飞书 P1 报警

### 约束

- 备用模式下的平仓操作必须写入决策端本地日志
- 决策端不得代替模拟交易端维护完整账本
- SimNow 凭证禁止硬编码，必须通过环境变量注入
- 备用模式不替代模拟交易端的正常运营
- 备用模式仅为应急保护机制

## 三、文件白名单（冻结）

| # | 文件路径 | 操作 | 说明 |
|---|---------|------|------|
| 1 | `services/decision/src/publish/failover.py` | 新建 | 健康探测 + 备用模式状态机 + CTP 仅平仓执行 |
| 2 | `services/decision/src/publish/sim_adapter.py` | 修改 | 添加 health_check() 方法 |
| 3 | `services/decision/src/publish/executor.py` | 修改 | 集成 failover 逻辑 |
| 4 | `services/decision/src/publish/__init__.py` | 修改 | 导出 failover |
| 5 | `services/decision/src/notifier/dispatcher.py` | 修改 | 添加 FAILOVER 事件类型 |
| 6 | `services/decision/tests/test_failover.py` | 新建 | 备用模式单元测试 |

## 四、前置条件

- TASK-0021 decision 基础功能闭环
- TASK-0023-A sim-trading 发布接口已对接
- 模拟交易端 Mini 部署稳定运行

## 五、变更记录

| 时间 | 操作 | 签名 |
|------|------|------|
| 2026-04-08 | 初始建档 | Atlas |
| 2026-04-13 | 白名单冻结（6 文件） | Atlas |
| 2026-04-13 | Token 签发 tok-e2c4419a（6 文件 / 4320min） | Jay.S |
| 2026-04-13 | Claude 执行完成（6 文件全部落地，10 测试全通过） | Claude |
| 2026-04-13 | Atlas 审核通过 | Atlas |
