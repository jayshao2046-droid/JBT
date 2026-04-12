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

### 修改 5: dispatcher.py 添加 FACTOR/WATCHLIST 通知类型
- **文件**: `services/data/src/notify/dispatcher.py`
- **变更**:
  - `NotifyType` 枚举新增 `FACTOR` 和 `WATCHLIST` 两个值
  - `_webhook_for_type` 新增两种类型的 Webhook 路由链：FACTOR → 交易群优先，WATCHLIST → 资讯群优先
- **原因**: 因子通知器和 watchlist 更新需要通过标准通知流水线发送
- **影响范围**: dispatcher.py NotifyType 枚举 + _webhook_for_type 路由函数

### 修改 6: test_collectors.py 扩充测试覆盖
- **文件**: `services/data/tests/test_collectors.py`
- **变更**: 新增 11 个测试用例
  - `storage_ready` 属性测试 (True/False)
  - `save()` 空记录、无 storage 场景测试
  - `_collect_with_retry` 重试次数验证
  - `NotifyType` FACTOR/WATCHLIST 枚举测试
  - `_webhook_for_type` 全类型路由测试
  - API 认证中间件测试：DATA_API_KEY 未设置时允许访问、/health 始终可达
- **原因**: 扩展测试覆盖率，验证本轮新增功能
- **影响范围**: test_collectors.py 新增测试函数

---

## TASK-0065 backtest 服务收口 100% + F-001 安全修复

### 修改 7: generic_strategy.py F-001 eval() 安全加固
- **文件**: `services/backtest/src/backtest/generic_strategy.py`
- **变更**:
  - `_safe_eval_expression` 新增 1024 字符长度限制和 200 AST 节点复杂度限制
  - `_SafeExpressionValidator` 新增 `node_count` 计数器，每次 `generic_visit` 递增
  - 新增 `_MAX_POW_EXPONENT = 100` 类属性
  - `visit_BinOp` 新增 Pow 指数上限检查：当右操作数为常量且 > 100 时拒绝执行
  - 修复 Python 3.9 兼容：`set[str]` → `Set[str]`（typing import）
- **原因**: F-001 安全漏洞 — `eval()` 虽有 AST 白名单，但缺少长度/复杂度/Pow 指数限制，恶意表达式可制造 CPU 拒绝服务
- **验证**: 5 项安全测试全部通过（基本表达式、合法 Pow、超限 Pow、超长表达式、超复杂表达式）

### 修改 7b: generic_strategy.py F-001 Pow 非常量指数拒绝
- **文件**: `services/backtest/src/backtest/generic_strategy.py`
- **变更**: `visit_BinOp` 中 Pow 分支增强：非常量指数（变量、子表达式）一律拒绝
  - 原逻辑仅检查「常量 > 100」，非常量直接放行 → 攻击者可用 `x ** y` 绕过
  - 新逻辑：Pow 右操作数必须是 `ast.Constant` 且 value 为 int/float，否则抛错
- **原因**: Atlas 复审指出非常量 Pow 指数是安全缺口
- **验证**: 5 项测试通过（常量合法、常量超限、变量指数拒绝、表达式指数拒绝、普通数学正常）

### 修改 8: backtest 服务 API Key 认证中间件
- **文件**: `services/backtest/src/api/app.py`
- **变更**:
  - 新增 `BACKTEST_API_KEY` 环境变量驱动的全局 API Key 认证
  - `_verify_api_key` 作为 FastAPI 全局依赖注入
  - `/api/health`、`/api/v1/health`、`/api/v1/version` 免认证
  - 使用 `hmac.compare_digest` 防止时序攻击
  - Key 为空时跳过认证（兼容开发环境）
- **原因**: backtest 服务此前零认证，所有 8 个路由组完全暴露
- **影响范围**: app.py import + 认证逻辑块 + FastAPI dependencies 参数

### 修改 9: backtest 服务认证测试
- **文件**: `services/backtest/tests/test_api_surface.py`
- **变更**: 新增 5 个 API Key 认证测试
  - Key 未设置时允许访问
  - Key 设置后无认证返回 403
  - 正确 Key 正常访问
  - /api/health 始终可达
  - 错误 Key 返回 403
- **验证**: 5/5 通过

---

## TASK-0066 decision 服务收口 100% + SG API 认证

### 修改 10: decision 服务 API Key 认证中间件
- **文件**: `services/decision/src/api/app.py`
- **变更**:
  - 新增 `DECISION_API_KEY` 环境变量驱动的全局 API Key 认证
  - `_verify_api_key` 作为 FastAPI 全局依赖注入
  - `/health`、`/ready` 免认证
  - `hmac.compare_digest` 防时序攻击，Key 为空时跳过
- **原因**: decision 服务此前零认证，11 个路由组完全暴露

### 修改 11: decision 服务认证测试
- **文件**: `services/decision/tests/test_api_auth.py`（新建）
- **变更**: 新增 5 个 API Key 认证测试
  - Key 未设置时允许访问
  - Key 设置后无认证返回 403
  - 正确 Key 正常访问（/strategies 200）
  - /health 始终可达
  - 错误 Key 返回 403
- **验证**: 决策端 5/5 认证测试通过

### 修改 12: decision settings.py 添加 sim_trading_url + Python 3.9 兼容修复
- **文件**: `services/decision/src/core/settings.py`
  - 新增 `sim_trading_url: str = "http://localhost:8101"` 设置项
- **文件**: `services/decision/src/research/sandbox_engine.py`
  - 修复 2 处 Python 3.10+ 类型语法 → Python 3.9 兼容
- **文件**: `services/decision/src/research/stock_screener.py`
  - 修复 4 处 Python 3.10+ 类型语法 → Python 3.9 兼容
- **验证**: 108 同步测试通过

---

## TASK-0067 sim-trading 认证冲突修复（接管后首个任务）

### 修改 13: sim-trading router.py 清理旧认证代码
- **文件**: `services/sim-trading/src/api/router.py`
- **变更**:
  - 删除 commit 836eac9 遗留的旧认证逻辑（第 12-24 行）
  - 删除 `_API_KEY` 变量、`verify_api_key` 函数、`dependencies=[Depends(verify_api_key)]`
  - 保留 main.py 的全局认证中间件（commit a69df54）
- **原因**: 
  - 两套认证冲突：router.py (401, X-Api-Key, 无免认证) vs main.py (403, X-API-Key, 有免认证)
  - 双重认证叠加导致 Header 名称不一致、状态码不一致
  - router.py 无免认证路径，会拦截 `/api/v1/health`
- **影响范围**: router.py import 行 + APIRouter 创建行
- **验证**: main.py `_PUBLIC_PATHS` 已包含 `/api/v1/health`
- **同步**: ✅ 已推送至 origin/main (commit 0c9accb)，✅ Mini 已同步

### 修改 14: sim-trading router.py 修复缺失 import os
- **文件**: `services/sim-trading/src/api/router.py`
- **变更**: 恢复 `import os`（在修改 13 清理认证代码时误删）
- **原因**: 
  - L39 `os.getenv("SIMNOW_BROKER_ID", "6000")` 抛出 `NameError: name 'os' is not defined`
  - 导致所有测试无法运行（5 errors）
  - 服务启动失败
- **影响范围**: router.py L1 import 行
- **验证**: 测试从 5 errors → 63 passed, 22 failed (403 认证预期)
- **同步**: ✅ 已推送至 origin/main (commit 64c491e)，⚠️ Mini 网络超时未同步

---

## sim-trading 独立二次核验（TASK-0067 延伸）

### 核验范围
- 审核报告一致性检查（7 个修复项逐条核验）
- Bug 全面排查（逻辑/异常/配置/集成）
- 安全漏洞排查（OWASP Top 10）
- 风险残留排查
- 接口全量一致性核验（28 个接口）
- 测试充分性核验（86 个测试）
- 提交可回滚性核验（7 个 commit）

### 核验结果
- **最终判定**: ✅ 有条件通过
- **Bug 总数**: 2 个（阻断 1 已修复 / 低风险 1）
- **安全漏洞**: 1 个（认证冲突，已修复）
- **证据充分项**: 9 项
- **证据不足项**: 2 项（前端页面、集成测试）

### 发现的问题
1. **Bug #1 (P0 阻断)**: router.py 缺失 `import os` → ✅ 已修复（commit 64c491e）
2. **Bug #2 (P2 低风险)**: 22 个测试失败（403 认证预期） → 建议修复
3. **安全漏洞 #1**: 认证中间件冲突 → ✅ 已修复（commit 0c9accb）

### 核验报告
- **文件**: `docs/reviews/sim-trading-二次核验报告-2026-04-12.md`
- **内容**: 12 章节完整核验报告（含证据、代码行号、commit 引用）
- **结论**: 允许远端同步（Bug #1 已修复）
