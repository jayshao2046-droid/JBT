# TASK-0065 — backtest 服务收口 100% + SG 安全修复（F-001）

【签名】Atlas  
【时间】2026-04-12  
【设备】MacBook  
【状态】✅ 执行完成，待 Atlas 复审

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0065 |
| 任务名称 | backtest 服务收口 100% + SG 安全修复（F-001） |
| 所属阶段 | Round 2 冲刺 / SG 安全治理横线 |
| 主责服务 | `services/backtest/` |
| 协同服务 | 无 |
| 执行 Agent | Claude-Code |
| 优先级 | P0 |
| 前置依赖 | TASK-0064 Round 1 Atlas 复审通过 ✅ |
| 状态 | ✅ 执行完成，待 Atlas 复审 |

## 任务背景

backtest 服务当前完成度 88%，存在 F-001 安全问题（generic_strategy.py eval 表达式执行链风险）。本任务目标：功能补全 + API 认证 → 88% 提升到 100%，同时完成 SG 安全修复 F-001。

## 文件级白名单（精确，共 3 项）

| # | 文件路径 | 改动目的 |
|---|---------|---------|
| 1 | `services/backtest/src/backtest/generic_strategy.py` | F-001 eval 安全加固（表达式长度限制、AST 深度限制、禁止 Pow 超大指数）|
| 2 | `services/backtest/src/api/app.py` | 添加 API Key 认证中间件 |
| 3 | `services/backtest/tests/test_api_surface.py` | 扩充认证测试 |

> ⚠️ F-001 安全修复（generic_strategy.py）的 commit 必须独立于功能 commit，不得合并。

## 验收标准

- [ ] `pytest services/backtest/tests/ -x -q` 全量通过
- [ ] F-001 eval 风险修复代码已独立 commit 并附代码证据
- [ ] API 认证中间件生效（未授权请求返回 401）
- [ ] 审核看板页面扩容（manual review / stock review）完成

## 收口流程

同 TASK-0064：改动→私有 prompt 留痕→独立 commit→积累后→append_atlas_log→Atlas 审查→Jay.S 确认→push→两地同步

## 执行结果

### Commit 1: 6477af2 — F-001 eval() 安全加固
- `_safe_eval_expression` 新增 1024 字符长度限制 + 200 AST 节点复杂度上限
- `_SafeExpressionValidator.visit_BinOp` 新增 Pow 指数 ≤100 检查
- 修复 Python 3.9 兼容：`set[str]` → `Set[str]`
- **验证**: 5 项安全测试通过（基本表达式、合法 Pow、超限 Pow 被拒、超长被拒、超复杂被拒）

### Commit 2: 6e4539d — API Key 全局认证中间件 + 5 项测试
- `app.py` 新增 `BACKTEST_API_KEY` 环境变量驱动认证，`hmac.compare_digest` 防时序攻击
- `/api/health`、`/api/v1/health` 免认证
- `test_api_surface.py` 新增 5 项测试全部通过

### 遗留项
- F-002 (subprocess) / F-003 (query) 不在白名单，留待 SG5
- `test_run_results_detail_and_progress_minimal_chain` 既有失败，非本轮引入
