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
