# Claude Code 全项目交接文档

**日期**：2026-04-12  
**发起方**：Jay.S / Atlas  
**接收方**：Claude Code  
**当前 HEAD**：`a69df54`（已推送至 origin/main）

---

## 一、项目概述

JBT 是一个多服务量化交易系统，从 legacy J_BotQuant 迁移到微服务架构。包含 6 个核心服务：

| 服务 | 端口 | 部署设备 | 当前完成度 | 目标 |
|------|------|---------|-----------|------|
| data | 8105 | Mini | **100%** | ✅ 已收口 |
| backtest | 8103 | Air | **95%** | 🟡 Pow 补丁已完成 |
| sim-trading | 8101 | Mini | **85%** | 🟡 需二次核验 |
| decision | 8104 | Studio | **80%** | 🟡 路由已修+认证已加 |
| dashboard | 8106 | Studio | **5%** | ❌ 后置 |
| live-trading | 8102 | Studio | **0%** | ❌ 最后阶段 |

---

## 二、已完成工作总览（本轮冲刺 20 个 commit）

### Round 0: sim-trading 安全修复（9 commits, 41ec077..1ecb83a）
- 已完成，已审核通过，已推送

### Round 1: data 服务 93%→100%（8 commits, 0e106c0..6e27866）— TASK-0064
- `main.py` DATA_API_KEY 全局认证中间件
- `base.py` 清除 A2 STUB
- `data_scheduler.py` 因子通知器+SLA 追踪器实现
- `health_check.py` 修复 FeishuNotifier 死代码
- `dispatcher.py` 新增 FACTOR/WATCHLIST 通知
- `test_collectors.py` 扩充 11 个测试
- Python 3.9 类型兼容修复
- **状态**：✅ 全部审核通过并推送

### Round 2: backtest 服务 88%→95%（2 commits, 6477af2..97f4888）— TASK-0065
- `generic_strategy.py` F-001 eval() 安全加固（长度/复杂度/Pow 三重限制）
- `generic_strategy.py` Pow 非常量指数拒绝补丁
- `app.py` BACKTEST_API_KEY 全局认证中间件
- `test_api_surface.py` 5 项认证测试
- **状态**：✅ 全部审核通过并推送

### Round 3: decision 服务 75%→80%（3 commits, 32e4d99..98cc5a7）— TASK-0066
- `app.py` DECISION_API_KEY 全局认证中间件 + 5 项测试
- `settings.py` 新增 sim_trading_url 配置
- `sandbox_engine.py` + `stock_screener.py` Python 3.9 类型兼容修复（6处）
- **状态**：✅ 已审核通过并推送

### Round 3 追加: decision 路由修复 + sim-trading 认证（2 commits, d49b6df..a69df54）
- **d49b6df**: `strategy.py` 将 /dashboard 和 /watchlist 静态路由移到 /{strategy_id} 之前，修复 404 bug
- **d49b6df**: `signal.py` 为 _decisions 内存字典添加持久化缺失注释
- **a69df54**: `sim-trading/main.py` 添加 SIM_API_KEY 全局认证中间件
- **a69df54**: `sim-trading/tests/test_api_auth.py` 新建 5 项认证测试
- **状态**：✅ 已推送。但有错误需要修正（见第三章）

---

## 三、需要修正的错误（P0 立即处理）

### 错误 1: sim-trading 认证中间件位置错误

**问题**：commit `a69df54` 将 SIM_API_KEY 认证加到了 `services/sim-trading/src/main.py`，但 sim-trading 的路由全部在 `services/sim-trading/src/api/router.py`。需要确认认证中间件是否正确覆盖了所有路由。

**验证方法**：
```bash
# 检查 main.py 中认证中间件的挂载方式
cat services/sim-trading/src/main.py | grep -A 20 "SIM_API_KEY"
# 对比 router.py 的路由注册
grep "router\." services/sim-trading/src/api/router.py | head -30
```

**注意**：sim-trading 在 commit `836eac9` 已经有一个 API Key 认证实现（早期 sim-trading 安全修复 Round 0）。需要检查 `a69df54` 的新认证是否与旧认证冲突/重复。如果重复，需要清理。

### 错误 2: 推送同步失败

**问题**：推送到 GitHub 成功，但 Mini 和 Studio 两地同步失败。

**修复命令**：
```bash
# Mini 同步
ssh jaybot@192.168.31.74 "cd ~/JBT && git fetch origin && git reset --hard origin/main"
# Studio 同步
ssh jayshao@192.168.31.142 "cd ~/JBT && git fetch origin && git reset --hard origin/main"
```

**注意**：执行前先确认网络连通性（Mini 报 HTTP2 framing error，Studio 报 SSH 连接关闭）。

---

## 四、待完成任务全景（按优先级排列）

### P0 — 立即执行

#### 4.1 修正上述两个错误
- 验证 sim-trading 认证中间件是否正确
- 完成 Mini + Studio 两地同步

#### 4.2 提交未提交的治理文件（不要修改内容，原样 commit）

以下文件有未提交修改或未跟踪，需要**原样提交**，不修改内容：

**已修改（Atlas 之前编辑的，原样 commit）：**
- `ATLAS_PROMPT.md` — Atlas 专属，Claude Code **不要编辑**此文件内容，只需原样 commit
- `docs/JBT_FINAL_MASTER_PLAN.md` — 同上，原样 commit

**未跟踪（需 git add 再 commit）：**
- `docs/reviews/PROJECT_STATUS_REPORT_2026-04-12.md`
- `docs/reviews/sim-trading-二次核验联络文档.md`
- `docs/tasks/TASK-0064-data服务收口100%+SG安全修复.md`
- `docs/tasks/TASK-0065-backtest服务收口100%+SG安全修复F001.md`
- `docs/tasks/TASK-0066-decision服务收口100%+SG安全修复.md`
- `docs/handoffs/CLAUDE_CODE_HANDOFF_2026-04-12.md`（本交接文档）

#### 4.3 更新 Claude Code 私有 prompt（持续维护）

**文件：`docs/prompts/agents/Claude-Code提示词.md`**

这是 Claude Code 的工作日志文件，之前已记录了修改 1~12。后续每做一项改动，都应在此文件追加记录（格式参考已有条目）。

> **重要**：ATLAS_PROMPT.md 由 Atlas 角色维护，Claude Code 只能通过 `append_atlas_log` MCP 工具追加日志（需 Token 覆盖）。日常改动留痕请写入 `docs/prompts/agents/Claude-Code提示词.md`。

### P1 — 本轮冲刺内完成

#### 4.5 sim-trading 二次核验
- 核验文档已准备：`docs/reviews/sim-trading-二次核验联络文档.md`
- 需要对 sim-trading 服务进行独立全量二次核验
- 核验范围：审核报告一致性、7 项修复逐条核验、Bug 排查、安全漏洞排查、28 个接口一致性、5 个看板页面、测试充分性
- **注意**：这是只读审核任务，不需要 Token

#### 4.6 SG5 统一安全修复预审
- SG1~SG4 已完成
- SG5 需要对所有已确认安全问题进行统一修复预审
- 已确认问题：
  - F-001: backtest eval() ✅ 已修复
  - F-002: data subprocess 风险（待 SG5 处理）
  - F-003: data 查询构造链风险（待 SG5 处理）

#### 4.7 decision 服务剩余收口（75%→100%）
- CB1/CB4~CB9 股票研究扩容
- CS1 本地 Sim 容灾
- CK1~CK3 因子双地同步
- signal.py _decisions 持久化（当前纯内存，重启丢失）

### P2 — 中期任务

#### 4.8 sim-trading 开盘验证（TASK-0017）
- 实盘环境下验证 CTP 交易流程
- 需要在交易时间进行

#### 4.9 TASK-0045 Mini macOS 容器自愈守护基线
- DR3 容器崩溃恢复
- Docker restart policy 配置

#### 4.10 各服务临时看板搭建
- sim-trading_web: 已有基本可用
- decision_web: 7 页面已闭环
- backtest_web: 需扩容 manual review / stock review 页面
- data_web: 待确认状态

### P3 — 后置任务

#### 4.11 dashboard 聚合看板（TASK-0015）
- 需等所有后端服务基本收口
- 聚合 6 服务状态到 dashboard:8106

#### 4.12 live-trading 实盘交易
- 待 sim-trading 稳定运行 2~3 个月后启动

---

## 五、治理规则提醒

### 5.1 写操作门禁
对 `services/**` 任何文件的写操作必须：
1. 任务在 `docs/tasks/` 登记
2. 架构师完成预审（`docs/reviews/` 有记录）
3. 文件在当前任务的白名单中
4. Jay.S 签发有效 Token（通过 `check_token_access` MCP 工具验证）

### 5.2 只读操作
- 读文件、搜索、诊断不需要 Token
- 发现需要写操作时，先停止，汇报最小文件范围

### 5.3 批次收口流程
1. 改动 → 私有 prompt 留痕 → 独立 commit
2. 调用 `append_atlas_log` 写批次摘要
3. 等 Atlas 复审 → 架构师终审 → lockback
4. 独立 commit → 两地同步

### 5.4 服务归属隔离
- 不同服务之间禁止跨服务 import（除 shared/contracts 和 shared/python-common）
- 每端一个 Token 白名单，不跨端

---

## 六、设备拓扑与端口（冻结）

| 设备 | 内网 IP | 蒲公英 IP | 服务 |
|------|---------|----------|------|
| MacBook | localhost | 172.16.3.136 | 全部开发环境 |
| Mini | 192.168.31.74 | 172.16.0.49 | data:8105, sim-trading:8101 |
| Air | 192.168.31.245 | — | backtest:8103 |
| Studio | 192.168.31.142 | 172.16.1.130 | decision:8104, dashboard:8106 |

---

## 七、关键文件路径

| 文件 | 用途 |
|------|------|
| `ATLAS_PROMPT.md` | Atlas 入口 prompt（当前状态+历史动作） |
| `docs/JBT_FINAL_MASTER_PLAN.md` | 终局总计划（63KB） |
| `PROJECT_CONTEXT.md` | 项目上下文与接管规则 |
| `WORKFLOW.md` | 工作流与角色权限矩阵 |
| `CLAUDE.md` | Claude Code 治理规则 |
| `docs/tasks/` | 任务预审单 |
| `docs/reviews/` | 审核记录 |
| `docs/locks/` | 锁控账本 |
| `docs/prompts/` | Agent prompt |
| `docs/prompts/agents/Claude-Code提示词.md` | Claude Code 私有 prompt |

---

## 八、当前 Token 状态

通过 `workflow_status` MCP 工具可查询活跃 Token。当前已签发且在有效期内的 Token：

| Token ID | 任务 | 服务 | 文件数 | 有效期 |
|----------|------|------|--------|--------|
| tok-5b40deb2 | TASK-0064 | data | 6 | 4320min |
| tok-f83d4d7b | TASK-0065 | backtest | 3 | 4320min |
| tok-b7688e4e | TASK-0066 | decision | 8 | 4320min |

> 注意：TASK-0064/0065 白名单内工作已全部完成。TASK-0066 白名单内工作已完成，strategy.py 和 signal.py 不在白名单但已有其他 Claude 实例通过追加 Token 完成修复（commit d49b6df）。

还有 Phase C Batch-5 的 6 枚 Token（TASK-0056~0059），状态需通过 `workflow_status` 确认。

---

## 九、Git 状态快照

```
当前分支: main
HEAD: a69df54 (sim-trading: 添加 SIM_API_KEY 全局 API 认证中间件 + 5 项认证测试)
origin/main: a69df54 (同步)

未提交修改:
 M ATLAS_PROMPT.md
 M docs/JBT_FINAL_MASTER_PLAN.md

未跟踪文件:
 ?? docs/reviews/PROJECT_STATUS_REPORT_2026-04-12.md
 ?? docs/reviews/sim-trading-二次核验联络文档.md
 ?? docs/tasks/TASK-0064-data服务收口100%+SG安全修复.md
 ?? docs/tasks/TASK-0065-backtest服务收口100%+SG安全修复F001.md
 ?? docs/tasks/TASK-0066-decision服务收口100%+SG安全修复.md

两地同步状态:
 ✅ GitHub: 已推送
 ❌ Mini (192.168.31.74): HTTP2 framing layer 错误
 ❌ Studio (192.168.31.142): SSH 连接关闭
```

---

## 十、执行建议

1. **先修正错误**：验证 sim-trading 认证是否重复/冲突，修复两地同步
2. **提交治理文件**：把未跟踪的 5 个文件 + 2 个已修改文件一次性 commit
3. **执行 sim-trading 二次核验**：这是只读任务，可立即开始
4. **后续按 P1→P2→P3 顺序推进**

---

*本文档由 Atlas 编制，作为 Claude Code 全项目接管的完整交接依据。*
