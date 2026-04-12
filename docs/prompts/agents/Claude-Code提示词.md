# Claude-Code 执行 Agent 私有 Prompt

【签名】Claude-Code
【时间】2026-04-12
【任务】TASK-0064 data 服务收口 100% + SG 安全修复

## 修改记录

### 修改 1: data 服务 API 认证中间件
- **文件**: `services/data/src/main.py`
- **变更**: 添加 `DATA_API_KEY` 环境变量认证中间件
  - 新增 `_verify_api_key` 依赖，作为 FastAPI 全局依赖注入
  - `/health`、`/api/v1/health`、`/api/v1/version` 免认证（公共健康检查）
  - 其他所有端点（bars、stocks/bars、symbols、dashboard/*、ops/*）需要 `X-API-Key` Header
  - `DATA_API_KEY` 为空时跳过认证（兼容开发环境）
  - 使用 `hmac.compare_digest` 防止时序攻击
- **原因**: SG 安全修复 — 所有业务端点此前完全无认证保护
- **影响范围**: main.py import 行 + app 创建 + 新增认证逻辑块

### 修改 2: base.py 清除 A2 STUB，转为正式延迟注入设计
- **文件**: `services/data/src/collectors/base.py`
- **变更**:
  - `TODO(A2)` 注释替换为正式的"延迟注入"设计说明
  - `storage=None` 时的 warning 降级为 debug（这是正常运行模式，非异常）
  - 新增 `storage_ready` 属性，方便调用方判断存储后端是否已注入
- **原因**: A2 存储迁移已收口，当前所有采集器通过 scheduler 的文件持久化路径存储，STUB 注释已过时
- **影响范围**: base.py 注释 + save() 日志级别 + 新增 property

### 修改 3: data_scheduler.py 因子通知器和 SLA 追踪器 STUB 替换为实际实现
- **文件**: `services/data/src/scheduler/data_scheduler.py`
- **变更**:
  - `get_factor_notifier()` 从 STUB 替换为通过 `NotifierDispatcher` 发送分时段报告到飞书
  - `get_sla_tracker()` 从 STUB 替换为基于 `collector_alarm_state.json` 统计活跃告警并发送 SLA 日报
  - 清理 3 处已过时的注释掉的 import 行
- **原因**: STUB 导致因子报告和 SLA 日报功能空转，现在接入真实的通知调度
- **影响范围**: data_scheduler.py 两个函数 + 3 处注释清理

### 修改 4: health_check.py 修复 legacy FeishuNotifier 死代码引用
- **文件**: `services/data/src/health/health_check.py`
- **变更**:
  - `send_p0_alert` 中的 fallback 从引用不存在的 `FeishuNotifier` 类替换为使用 `FeishuSender.send_card` 直接发送原始卡片
  - 保持 fallback 逻辑：新通知系统失败时退回到原始卡片方式
- **原因**: `FeishuNotifier` 类已在新通知系统迁移时移除，旧 fallback 代码会抛出 NameError
- **影响范围**: health_check.py send_p0_alert 函数的 except 分支
- **SG 备注**: F-002(subprocess)/F-003(query) 涉及的文件 (storage.py/health_remediate.py) 不在当前 Token 白名单，留待 SG5 统一修复
