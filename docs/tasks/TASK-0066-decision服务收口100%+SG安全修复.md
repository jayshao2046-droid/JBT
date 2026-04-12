# TASK-0066 — decision 服务收口 100% + SG 安全修复

【签名】Atlas  
【时间】2026-04-12  
【设备】MacBook  
【状态】⚠️ 白名单内执行完成，需追加 Token 修复路由 bug

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0066 |
| 任务名称 | decision 服务收口 100% + SG 安全修复 |
| 所属阶段 | Round 3 冲刺 / SG 安全治理横线 |
| 主责服务 | `services/decision/` |
| 协同服务 | 无 |
| 执行 Agent | Claude-Code |
| 优先级 | P0 |
| 前置依赖 | TASK-0065 Round 2 |
| 状态 | ⚠️ 白名单内执行完成，需追加 Token |

## 任务背景

decision 服务当前完成度 75%，差距最大。待办：CB1/CB4~CB9 股票研究扩容、CS1 容灾、CK1~CK3 因子同步，加 SG API 认证。由 Claude Code 扫描后精确实施。

## 文件级白名单（首批 8 项，Claude Code 如需追加再申请）

| # | 文件路径 | 改动目的 |
|---|---------|---------|
| 1 | `services/decision/src/api/app.py` | API 认证中间件（SG 安全） |
| 2 | `services/decision/src/main.py` | 主入口配置 |
| 3 | `services/decision/src/core/signal_dispatcher.py` | 信号分发完善 |
| 4 | `services/decision/src/research/sandbox_engine.py` | 沙箱引擎完善 |
| 5 | `services/decision/src/research/stock_screener.py` | 全 A 选股完善 |
| 6 | `services/decision/src/gating/research_gate.py` | 研究门控逻辑 |
| 7 | `services/decision/src/core/settings.py` | 配置扩展 |
| 8 | `services/decision/tests/test_api_auth.py` | API 认证测试 |

> ⚠️ 如 Claude Code 扫描后发现需要额外文件，须提交补充 Token 申请。

## 收口流程

同 TASK-0064/0065：改动→私有 prompt 留痕→独立 commit→积累后→append_atlas_log→Atlas 审查→Jay.S 确认→push→两地同步

## 执行结果

### Commit 1: 32e4d99 — API Key 全局认证中间件 + 5 项测试
- `app.py` 新增 `DECISION_API_KEY` 环境变量驱动认证，`hmac.compare_digest` 防时序攻击
- `/health`、`/ready` 免认证
- 新建 `test_api_auth.py` 5 项认证测试全部通过

### Commit 2: 98cc5a7 — sim_trading_url 配置 + Python 3.9 兼容
- `settings.py` 新增 `sim_trading_url: str = "http://localhost:8101"` 正式配置
- `sandbox_engine.py` 修复 2 处 Python 3.10+ 类型语法
- `stock_screener.py` 修复 4 处 Python 3.10+ 类型语法

### 本地端点验证（127.0.0.1:8104）

| 端点 | 状态 | 数据质量 |
|------|------|----------|
| `/health` | 200 | 正常 |
| `/ready` | 200 | 正常 |
| `/strategies/overview` | 200 | KPI + pipeline + blockers 完整 |
| `/strategies` | 200 | 策略列表正常 |
| `/strategies/dashboard` | **404** | 路由优先级 bug（需修 strategy.py）|
| `/strategies/watchlist` | **404** | 同上 |
| `/signals/overview` | 200 | KPI 6 维度完整 |
| `/signals` | 200 | 空（正常，无信号时） |
| `/signals/dashboard/*` | 200 | 3 子端点正常 |
| `/models/runtime` | 200 | 运行时快照完整 |
| `/models/status` | 200 | 设置信息正常 |
| `/models/dashboard` | 200 | 2 模型 profile 正常 |

### 需追加 Token 的遗留项

1. **`services/decision/src/api/routes/strategy.py`** — **路由优先级 bug**
   - `GET /strategies/{strategy_id}` 在 line 284 注册，吞掉了后面的 `/strategies/dashboard`（352）和 `/strategies/watchlist`（369）
   - 修复方案：将静态路径注册移到参数路径之前
   
2. **`services/decision/src/api/routes/signal.py`** — **signal decisions 持久化**
   - `_decisions` 纯内存 dict，重启丢失
   - 修复方案：接入 `state_store` 新增 `decisions` bucket

3. **`services/decision/src/api/routes/approval.py`** — **缺少 GET /approvals 列表端点**
   - 当前只能按 ID 查询，无法列出所有待审批项
