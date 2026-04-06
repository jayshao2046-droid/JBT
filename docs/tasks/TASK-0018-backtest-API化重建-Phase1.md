# TASK-0018 backtest API 化重建 Phase1 预审（双引擎并行升级）

## 文档信息

- 任务 ID：TASK-0018
- 文档类型：新任务预审与分批冻结
- 签名：项目架构师
- 建档时间：2026-04-07
- 设备：MacBook

---

## 一、任务目标

围绕“保留现有 TqSdk/TqBacktest 回测系统 + 新增 local 自建回测系统”建立 Phase1 正式任务边界：

1. 保留现有 TqSdk/TqBacktest 在线回测系统，作为 engine_type=`tqsdk` 路径。
2. 新增一套 local 自建回测系统，作为 engine_type=`local` 路径。
3. 在 backtest 看板增加“引擎选择按钮/开关”，可选择执行 `tqsdk` 或 `local`。
4. local 自建引擎必须与系统级风控完整联动，并与 tqsdk 路径共用风控事件模型。
5. 报告支持完整导出与展示，两引擎统一报告 schema。

本轮仅做建档预审，不写任何服务业务代码。

---

## 二、归属与边界

### 服务归属

1. 数据供给与 API 面归属 `services/data/**`。
2. 回测执行与 API 适配层归属 `services/backtest/**`。
3. 跨服务字段与接口语义归属 `shared/contracts/**`（先契约后实现）。

### 硬性边界

1. 不得跨服务 import 业务代码。
2. 跨服务联动只能通过 API，不得直接读取对方数据目录。
3. `runtime/`、`logs/`、真实 `.env`、数据库快照、账本文件属于禁改区。
4. 任一批次不得顺手修复无关问题，不得扩展任务范围。

---

## 三、双引擎并行架构与引擎选择器

1. 执行编排采用“双引擎并行架构”：
   - `engine_type=tqsdk`：沿用既有 `TqApi(backtest=TqBacktest(...), auth=TqAuth(...))` 主路径。
   - `engine_type=local`：新增本地自建回测执行路径。
2. 对外统一任务模型：同一任务入口、同一状态机、同一风控事件模型、同一报告 schema。
3. backtest_web 增加引擎选择器（按钮/开关）：默认值与回显逻辑必须显式可见，禁止隐式切换。

---

## 四、批次拆分（A~F）

### 批次 A（P0）：契约补充（只定义，不实现）

- 目标：在 `shared/contracts/backtest/api.md` 增补双引擎与证据链契约。
- 边界：仅定义字段、请求响应、错误码、版本策略；不写任何服务实现代码。
- 白名单示例：
  1. `shared/contracts/backtest/api.md`
- 验收标准：
  1. 明确 `engine_type` 字段：允许值至少包含 `tqsdk`、`local`，并定义默认值规则。
  2. 增补风控事件证据结构：至少覆盖输入快照、规则命中、执行动作、结果状态。
  3. 增补报告导出结构：定义导出格式、报告元信息、两引擎统一字段集合。
  4. 无任何 `services/**` 目录写入。
- 禁止项：
  1. 不得在契约中绑定某服务内部实现细节。
  2. 不得越权新增未评审字段。
  3. 不得删除或破坏既有 tqsdk 路径契约兼容性。

### 批次 B（P1）：data 服务最小只读 API

- 目标：在 `services/data/**` 提供最小 data-provider API（bars/symbols/health/version）。
- 边界：只读接口、最小鉴权与最小错误处理，不进入策略逻辑。
- 白名单示例：
  1. `services/data/src/**`
  2. `services/data/tests/**`
- 验收标准：
  1. 四个接口均可稳定返回。
  2. 接口行为与批次 A 契约一致。
  3. 不读取/不改写其他服务目录。
- 禁止项：
  1. 不得跨服务 import。
  2. 不得写入运行态敏感路径。

### 批次 C（P1）：backtest 双引擎执行编排层

- 目标：在 `services/backtest/**` 建立双引擎执行编排（保留 tqsdk + 新增 local），并统一任务模型。
- 边界：仅编排层与任务模型统一，不做额外产品功能扩展。
- 白名单示例：
  1. `services/backtest/src/**`
  2. `services/backtest/tests/**`
- 验收标准：
  1. `engine_type=tqsdk` 路径保持可用，不回退现有能力。
  2. `engine_type=local` 路径可执行最小回测闭环。
  3. 两引擎共用统一任务模型（任务创建、状态流转、错误语义一致）。
- 禁止项：
  1. 不得移除或替换 tqsdk 既有主路径。
  2. 不得引入跨服务业务模块依赖。

### 批次 D（P1）：系统级风控联动层（双引擎共用）

- 目标：建立双引擎共用风控核心与同一风控事件模型，确保 local 与 tqsdk 风控语义一致。
- 边界：仅限系统级风控联动，不扩展为策略重写。
- 白名单示例：
  1. `services/backtest/src/**`
  2. `services/backtest/tests/**`
- 验收标准：
  1. 两引擎共用同一风控核心，风控事件结构一致。
  2. 风控证据链可追溯：输入、规则命中、执行动作、结果状态完整。
  3. 同一输入下两引擎风控结论可解释（允许数值差异，但语义一致）。
- 禁止项：
  1. 不得把联动层扩大为全量策略重构。
  2. 不得改动白名单外文件。

### 批次 E（P1）：backtest_web 引擎选择控件与执行入口

- 目标：在 `services/backtest/backtest_web/**` 增加引擎选择控件（按钮/开关）与统一执行入口。
- 边界：仅处理引擎选择、任务发起、状态展示的最小闭环。
- 白名单示例：
  1. `services/backtest/backtest_web/app/**`
  2. `services/backtest/backtest_web/src/**`
- 验收标准：
  1. 页面提供显式 `tqsdk/local` 引擎选择器并可回显。
  2. 选择后可触发对应引擎执行，任务状态可区分引擎来源。
  3. 默认引擎策略可见且可审计，避免误触发错误默认值。
- 禁止项：
  1. 不得越权修改 backtest_web 白名单外文件。
  2. 不得引入真实凭证到前端代码。

### 批次 F（P1）：完整报告导出与展示（统一 schema）

- 目标：建立两引擎统一报告 schema 的完整导出与展示能力。
- 边界：仅报告结构、导出与展示链路，不扩展交易执行逻辑。
- 白名单示例：
  1. `services/backtest/src/**`
  2. `services/backtest/tests/**`
  3. `services/backtest/backtest_web/src/**`
  4. `services/backtest/backtest_web/app/**`
- 验收标准：
  1. 两引擎输出统一报告字段集合，支持完整展示。
  2. 支持完整导出（文件/结构校验可通过），并保留风控证据链关联。
  3. 同一任务在 UI 与导出文件中的关键指标一致。
- 禁止项：
  1. 不得新增白名单外导出通道。
  2. 不得仅对单一引擎实现报告 schema。

---

## 五、Token 与执行规则

1. 当前轮次仅建档：仅写 `docs/**` 与 prompt，不申请代码 Token。
2. A 批涉及 `shared/contracts/**`，执行前必须 P0 预审通过并获得文件级 Token。
3. B~F 批涉及 `services/**`，执行前必须按批次冻结文件级白名单并签发 P1 Token。
4. 每批执行后必须：自校验 -> 架构师终审 -> 锁回 -> prompt 同步。

---

## 六、统一禁止项

1. 禁止跨服务 import 业务代码。
2. 禁止跨服务直接读写数据目录。
3. 禁止修改 `runtime/`、`logs/`、真实 `.env`、数据库快照、账本数据。
4. 禁止在未获对应 Token 时修改保护路径。

---

## 七、预审结论

1. `TASK-0018` 正式成立。
2. 当前状态为“建档预审通过，待分批 Token”。
3. 后续执行顺序建议：A -> C -> D -> E -> F，B 可并行但必须在 C 接口冻结前完成契约对齐。
