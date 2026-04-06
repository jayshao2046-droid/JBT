# TASK-0010 sim-trading 服务骨架实现预审

## 文档信息

- 任务 ID：TASK-0010
- 文档类型：新任务预审与范围冻结
- 签名：项目架构师
- 建档时间：2026-04-06
- 设备：MacBook

---

## 一、任务目标

在 `TASK-0009` 严格风控冻结完成后，于 `services/sim-trading/**` 内建立最小可运行的服务骨架，为后续 SimNow 接入与严格风控实现提供正式落点。

本任务只允许做骨架与占位，不允许提前实现完整交易逻辑、legacy 兼容逻辑或跨服务读写。

本任务的最小结果必须同时满足：

1. 存在最小服务入口与健康检查能力。
2. 存在 API、execution、ledger、risk、gateway 五层骨架。
3. 风控钩子至少预留三类占位：只减仓模式、灾难止损、最小告警通道。
4. 不触碰 `shared/contracts/**` 与 `integrations/**`。

---

## 二、任务编号与归属结论

### 编号结论

- **本事项独立建档为 `TASK-0010`，不得继续并入 `TASK-0002`。**

### 判定理由

1. `TASK-0002` 阶段一已锁回；其后续服务实现需要新的 P1 白名单与独立锁控。
2. 当前事项只归属于 `services/sim-trading/**`，与 `TASK-0011` 的 legacy 运维清退、`TASK-0012` 的桥接兼容层不属于同一服务边界。
3. 服务骨架的 Token、验证方式与回滚路径都应独立，不得与 legacy 运维动作或桥接契约混用。

### 服务归属结论

- **任务归属：`services/sim-trading/**` 单服务范围。**

### 执行 Agent

1. 预审：项目架构师
2. 实施：模拟交易 Agent

### 强制边界

1. 不得修改 `shared/contracts/**`。
2. 不得修改 `integrations/**`。
3. 不得直接 import 其他服务 `src` 模块。
4. 不得复制 legacy 交易逻辑进入 `services/sim-trading/`。

---

## 三、前置依赖

1. `TASK-0009` 已闭环。
2. `TASK-0013` 已完成统一风控核心与 stage preset 治理冻结。
3. Jay.S 已按保护级别分别为模拟交易 Agent 签发 P0 / P1 Token。
4. 执行中若发现需要新增 `shared/contracts/**`、`integrations/**`、根级 `docker-compose.dev.yml`、`shared/python-common/**` 或第 16 个以上骨架文件，必须立即暂停并回交补充预审。

---

## 四、只读现状结论

基于当前仓内只读复核，得到以下结论：

1. `services/sim-trading/src/` 当前为空目录。
2. `services/sim-trading/tests/` 当前为空目录。
3. `services/sim-trading/configs/` 当前为空目录。
4. 仓内当前实际存在的环境模板文件为 `services/sim-trading/.env.example`，而不是 `services/sim-trading/configs/.env.example`。
5. `services/sim-trading/README.md` 已存在，且已冻结服务边界为“只负责 SimNow 模拟交易”。

---

## 五、最小文件白名单冻结

### 总表

1. `services/sim-trading/src/main.py`
2. `services/sim-trading/src/api/__init__.py`
3. `services/sim-trading/src/api/router.py`
4. `services/sim-trading/src/execution/__init__.py`
5. `services/sim-trading/src/execution/service.py`
6. `services/sim-trading/src/ledger/__init__.py`
7. `services/sim-trading/src/ledger/service.py`
8. `services/sim-trading/src/risk/__init__.py`
9. `services/sim-trading/src/risk/guards.py`
10. `services/sim-trading/src/gateway/__init__.py`
11. `services/sim-trading/src/gateway/simnow.py`
12. `services/sim-trading/.env.example`
13. `services/sim-trading/README.md`
14. `services/sim-trading/tests/test_health.py`
15. `services/sim-trading/tests/test_risk_hooks.py`

### 关于 `.env.example` 路径的治理结论

1. Atlas 派发口径中写为“`configs/.env.example`”。
2. 但仓内当前实际保护文件为 `services/sim-trading/.env.example`，且 `WORKFLOW.md` 将各服务根级 `.env.example` 视为 P0 保护路径。
3. 因此本次预审**暂按仓内现状冻结 `services/sim-trading/.env.example`**。
4. 若后续坚持新建或迁移到 `services/sim-trading/configs/.env.example`，必须另行提交 create/rename 补充预审，不能在当前批次顺手改动。

---

## 六、按工作流拆批结论

由于 `WORKFLOW.md` 规定默认单任务单批最多 5 个业务文件，且 `services/*/.env.example` 属 P0 保护路径，本任务虽归属同一任务号，但必须拆为 **1 个 P0 批次 + 3 个 P1 批次** 执行。

### 批次 A0：环境模板占位（P0）

1. `services/sim-trading/.env.example`

目标：只冻结占位符、字段说明与最小安全默认值，不写入任何真实凭证。

### 批次 A1：入口与 API 骨架（P1）

1. `services/sim-trading/src/main.py`
2. `services/sim-trading/src/api/__init__.py`
3. `services/sim-trading/src/api/router.py`
4. `services/sim-trading/README.md`

目标：建立最小服务入口、健康检查接口和环境模板口径。

### 批次 B：execution / ledger 骨架（P1）

1. `services/sim-trading/src/execution/__init__.py`
2. `services/sim-trading/src/execution/service.py`
3. `services/sim-trading/src/ledger/__init__.py`
4. `services/sim-trading/src/ledger/service.py`
5. `services/sim-trading/tests/test_health.py`

目标：建立执行链与账本骨架，并补最小健康测试占位。

### 批次 C：risk / gateway 骨架与风控钩子占位（P1）

1. `services/sim-trading/src/risk/__init__.py`
2. `services/sim-trading/src/risk/guards.py`
3. `services/sim-trading/src/gateway/__init__.py`
4. `services/sim-trading/src/gateway/simnow.py`
5. `services/sim-trading/tests/test_risk_hooks.py`

目标：建立风险与网关骨架，冻结三类风控钩子占位，并为未来 Mini 部署前的“断网 / 断数据源下本地缓存行为验证”预留最小测试入口。

### 当前继续锁定的路径

1. `shared/contracts/**`
2. `integrations/**`
3. `services/sim-trading/configs/**`
4. `services/sim-trading/tests/**` 白名单外文件
5. 其他全部非白名单文件

---

## 七、风控钩子占位要求

1. 必须显式保留 `reduce_only` 或同等语义的只减仓模式入口，不得等到后续补做。
2. 必须显式保留 `disaster_stop` 或同等语义的系统灾难止损入口。
3. 必须显式保留最小告警通道接口，哪怕当前只输出统一结构日志。
4. 这些钩子当前可以是 placeholder，但名称、调用位置和测试占位必须先固定。
5. `services/sim-trading/src/risk/**` 不得直接依赖 SimNow 专属报单 / 回报细节；任何 SimNow 专属调用只能留在 `services/sim-trading/src/gateway/simnow.py` 或同等适配层。
6. stage preset 的读取与切换口径必须与 `TASK-0013` 保持一致，不得在本任务中先硬编码出仅供 SimNow 使用的一套风控阈值分支。
7. 当前骨架阶段不要求实现完整本地缓存逻辑，但必须在风险骨架或测试占位中预留“断网 / 断数据源下的本地缓存行为验证”入口，供未来 Mini 部署前验证复用。
8. 该验证点属于系统级风控执行验证细节，不构成新增规则，也不意味着本批次需要提前实现缓存持久化。
9. 后续验证目标冻结为：Mini 断网或上游数据源中断时，Studio 侧 L1 / L2 决策要么读取最近一次本地快照继续做安全降级判断，要么拒绝开仓并进入 Fail-Safe，且不得 crash，不得产出错误交易信号。

---

## 八、最小验收标准

1. `services/sim-trading/src/main.py` 可返回最小健康检查 `200`。
2. API、execution、ledger、risk、gateway 五层目录均有最小占位文件。
3. 风控三钩子（只减仓、灾难止损、最小告警通道）已在代码骨架中保留明确落点。
4. 不存在跨服务 import。
5. 不存在 legacy 兼容逻辑进入 `services/sim-trading/`。
6. 风控层与网关层边界清晰，风险判断骨架未直接绑定 SimNow 专属 API 细节。
7. 当前骨架与测试占位已为未来 Mini 部署前的“断网 / 断数据源下的本地缓存行为验证”预留检查点，不要求本批次立即实现缓存逻辑。
8. 后续进入 Mini 部署前验证时，必须覆盖“读取最近一次本地快照或安全拒绝开仓进入 Fail-Safe，且不 crash、不产出错误信号”的测试点。

---

## 九、敏感信息治理

1. SimNow 账号、密码、柜台地址、鉴权字段只能作为运行时 Secret 注入，不得写入 Git、`.env.example`、README 或治理账本。
2. `.env.example` 只能保留占位符、字段说明与最小安全默认值，不得写入真实值。
3. 任何来自 J_BotQuant 的配置方案只能登记来源与接入方式，不能把真实密钥或真实账户信息写入仓库。

---

## 十、Token 建议

1. 本任务必须由模拟交易 Agent 分 4 批申请 Token，其中批次 A0 为单文件 P0，批次 A1 / B / C 为 P1。
2. 任一批次若发现需要改第 6 个文件，当前 Token 立即失效，必须返回补充预审。
3. 任一批次若发现必须新增 `shared/contracts/**` 或 `integrations/**` 触点，当前任务立即暂停。
4. 若坚持把环境模板迁移到 `services/sim-trading/configs/.env.example`，必须先做 create / rename 补充预审，再重新申请对应 Token。

---

## 十一、预审结论

1. **`TASK-0010` 正式成立。**
2. **本任务只归属 `services/sim-trading/**`，不得与 legacy 清退或桥接任务混并。**
3. **本任务最小白名单已冻结为 15 个文件，并按工作流拆分为 1 个 P0 批次 + 3 个 P1 批次。**
4. **本任务执行时必须遵守 `TASK-0013` 冻结的“同一风控核心 + 不同执行端适配层”原则，不得先写出仅供 SimNow 使用的一套长期风控核心。**
5. **环境模板当前按仓内现状冻结为 `services/sim-trading/.env.example`；若要改成 `configs/.env.example`，需 Jay.S 确认后另行补审。**
