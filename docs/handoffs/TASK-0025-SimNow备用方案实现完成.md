# TASK-0025 SimNow 备用方案实现完成

**任务**: TASK-0025-decision-SimNow备用方案-仅平仓模式  
**执行**: Claude  
**Token**: tok-e2c4419a  
**完成时间**: 2026-04-13

## 实现摘要

已完成 SimNow 备用方案的完整实现，包括状态机、健康检查、仅平仓约束和通知集成。

## 修改文件清单

### 新增文件
1. **services/decision/src/publish/failover.py** (177 行)
   - `FailoverManager` 类：状态机管理（NORMAL → FAILOVER → RECOVERING → NORMAL）
   - `FailoverState` 枚举：三态状态机
   - 健康检查：定期探测 sim-trading 服务
   - 仅平仓约束：FAILOVER 状态下拒绝开仓，仅接受平仓
   - SimNow 凭证管理：从环境变量读取（不硬编码）
   - 通知失败记录：记录最近 50 条通知失败事件

2. **services/decision/tests/test_failover.py** (177 行)
   - 10 个测试用例，全部通过 ✅
   - 覆盖状态机转换、仅平仓约束、健康检查、凭证管理

### 修改文件
3. **services/decision/src/publish/executor.py**
   - 集成 `FailoverManager`
   - 在 `publish_strategy()` 中添加备用方案逻辑
   - sim-trading 发布失败时自动切换到 FAILOVER 状态

4. **services/decision/src/publish/__init__.py**
   - 导出 `FailoverManager` 和 `FailoverState`

5. **services/decision/src/notifier/dispatcher.py**
   - 添加 `failover_manager` 可选参数
   - `dispatch()` 方法中集成通知失败记录
   - `runtime_snapshot()` 包含 failover 状态

6. **services/decision/src/publish/sim_adapter.py**
   - 已有 `health_check()` 方法，无需修改（TASK-0021 G batch 已实现）

## 测试结果

```
============================= test session starts ==============================
tests/test_failover.py::test_failover_state_machine_normal_to_failover PASSED [ 10%]
tests/test_failover.py::test_failover_state_machine_failover_to_recovering PASSED [ 20%]
tests/test_failover.py::test_failover_state_machine_recovering_to_normal PASSED [ 30%]
tests/test_failover.py::test_close_position_rejects_open PASSED          [ 40%]
tests/test_failover.py::test_close_position_accepts_close PASSED         [ 50%]
tests/test_failover.py::test_health_check_success PASSED                 [ 60%]
tests/test_failover.py::test_health_check_failure PASSED                 [ 70%]
tests/test_failover.py::test_credentials_from_env PASSED                 [ 80%]
tests/test_failover.py::test_close_position_requires_credentials PASSED  [ 90%]
tests/test_failover.py::test_sim_adapter_health_check PASSED             [100%]

============================== 10 passed in 0.15s
```

## 核心功能验证

### 1. 状态机转换 ✅
- NORMAL → FAILOVER：连续 3 次健康检查失败
- FAILOVER → RECOVERING：健康检查恢复成功
- RECOVERING → NORMAL：连续 2 次健康检查成功

### 2. 仅平仓约束 ✅
- FAILOVER 状态下拒绝开仓请求（返回 `failover_mode_open_rejected`）
- FAILOVER 状态下接受平仓请求（返回 `failover_close_submitted`）

### 3. 健康检查 ✅
- 成功：sim-trading `/health` 返回 200
- 失败：连接超时或 HTTP 错误

### 4. 凭证管理 ✅
- 从环境变量读取：`SIMNOW_BROKER_ID`, `SIMNOW_USER_ID`, `SIMNOW_PASSWORD`, `SIMNOW_TD_FRONT`
- 缺少凭证时返回 `simnow_credentials_missing`

### 5. 通知集成 ✅
- `NotifierDispatcher` 在双通道失败时调用 `failover.record_notification_failure()`
- `runtime_snapshot()` 包含 failover 状态

## 环境变量配置

需要在 `services/decision/.env` 中添加：

```bash
# SimNow 备用方案凭证（生产环境需配置真实值）
SIMNOW_BROKER_ID=9999
SIMNOW_USER_ID=your_user_id
SIMNOW_PASSWORD=your_password
SIMNOW_TD_FRONT=tcp://180.168.146.187:10130

# 健康检查配置（可选）
FAILOVER_PROBE_INTERVAL=60        # 探测间隔（秒）
FAILOVER_FAIL_THRESHOLD=3         # 失败阈值
FAILOVER_RECOVER_THRESHOLD=2      # 恢复阈值
```

## 下一步建议

1. **集成到 main.py**：在决策服务启动时初始化 `FailoverManager`
2. **监控集成**：将 failover 状态暴露到 `/health` 端点
3. **告警配置**：FAILOVER 状态触发 P0 告警
4. **文档更新**：更新运维手册，说明 SimNow 备用方案的使用场景

## 风险与限制

1. **SimNow 凭证安全**：生产环境需使用密钥管理服务（如 AWS Secrets Manager）
2. **仅平仓约束**：FAILOVER 状态下无法开新仓，可能影响策略执行
3. **健康检查延迟**：默认 60 秒探测间隔，故障切换有延迟
4. **CTP 连接稳定性**：SimNow 7x24 环境可能存在连接不稳定问题

## 验收标准

- [x] 状态机转换逻辑正确
- [x] 仅平仓约束生效
- [x] 健康检查功能正常
- [x] 凭证从环境变量读取
- [x] 通知失败记录功能
- [x] 单元测试全部通过（10/10）
- [ ] 集成测试（需 Atlas 安排）
- [ ] 生产环境凭证配置（需 Jay.S 审批）

---

**签名**: Claude  
**待复审**: Atlas  
**待终审**: 项目架构师
