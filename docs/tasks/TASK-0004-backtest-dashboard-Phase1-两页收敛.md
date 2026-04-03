# TASK-0004 backtest 看板 Phase1 两页收敛

## 文档信息

- 任务 ID：TASK-0004
- 文档类型：新任务预审与范围冻结
- 签名：项目架构师
- 建档时间：2026-04-03
- 设备：MacBook

---

## 一、任务目标

在 `services/backtest/V0-backtext 看板/` 目录内，将现有 Next.js 原型收敛为仅保留两类页面：

1. 策略管理
2. 回测详情

本轮补充冻结要求如下：

1. 首页默认直接进入“策略管理”，不再保留二选一中转页。
2. 现有其余页面本轮不进入实现范围。
3. 默认优先“停止引用 / 停用导航”，而不是删除文件。
4. 本轮目标是形成可在浏览器中演示的最小看板版本，便于 Jay.S 边看边指导。

---

## 二、服务归属与边界判定

### 归属结论

- **任务归属：`services/backtest/` 单服务范围内的看板原型收敛。**

### 判定理由

1. 当前目标目录位于 `services/backtest/` 下，而不是 `services/dashboard/`。
2. 本轮工作仅调整现有回测看板原型的页面入口与页面展示，不涉及跨服务数据聚合或独立 dashboard 服务建设。
3. 本轮不改 backtest 引擎、契约、Docker、其他服务，因此不构成跨服务任务。

### 强制边界

1. 本轮只允许落在 `services/backtest/V0-backtext 看板/`。
2. 不得扩展到 `services/backtest/src/**`、`services/backtest/tests/**`、`shared/contracts/**`、`docker-compose.dev.yml`、`.env.example`、其他服务目录。
3. 本轮不允许删除现有非目标页面文件，除非后续补充预审证明“不删无法达成目标”。
4. 若执行中发现需要新增第 4 个业务文件，必须重新提交补充预审，未经复审不得扩白名单。

---

## 三、只读现状结论

基于当前只读扫描与本次复核，得到以下结论：

1. `app/page.tsx` 当前是一个单页壳层，通过内部 state 切换 5 个 section：回测总览、策略管理、回测详情、风控监控、系统状态。
2. `app/agent-network/page.tsx` 已具备“策略管理”原型主体，可直接作为第一类保留页面基础。
3. `app/operations/page.tsx` 已具备“回测详情”原型主体，可直接作为第二类保留页面基础。
4. `app/layout.tsx` 当前仅提供全局字体、metadata 与 body 外壳，本轮不是阻塞项。
5. `package.json` 现有依赖与脚本已足够支撑本轮两页收敛，不需要本轮纳入白名单。
6. `app/command-center/`、`app/intelligence/`、`app/systems/` 可通过停止引用与停用导航方式退出本轮视图，不必删除文件。

---

## 四、本轮最小白名单冻结

### P1 业务文件白名单

1. `services/backtest/V0-backtext 看板/app/page.tsx`
2. `services/backtest/V0-backtext 看板/app/agent-network/page.tsx`
3. `services/backtest/V0-backtext 看板/app/operations/page.tsx`

### 当前明确不纳入白名单的文件

1. `services/backtest/V0-backtext 看板/app/layout.tsx`
2. `services/backtest/V0-backtext 看板/package.json`
3. `services/backtest/V0-backtext 看板/app/command-center/page.tsx`
4. `services/backtest/V0-backtext 看板/app/intelligence/page.tsx`
5. `services/backtest/V0-backtext 看板/app/systems/page.tsx`
6. 其余 `components/**`、`lib/**`、样式与配置文件

### 不纳入白名单的理由

1. 首页默认入口与导航收敛可在 `app/page.tsx` 内完成。
2. 两个目标页面主体已存在，优先在现有页面内做最小调整。
3. `layout.tsx` 与 `package.json` 当前不构成本轮实现阻塞；若先放入白名单，只会扩大风险半径。
4. 其余三类页面默认以“停止引用”收口，不需要本轮删除或改写。

---

## 五、执行 Agent 建议

### 合规默认建议

- **建议执行 Agent：回测 Agent。**

### 理由

1. 目标文件位于 `services/backtest/`，按当前服务边界应由回测 Agent 执行。
2. 本轮虽然是看板原型，但尚未迁入 `services/dashboard/`，不宜在预审阶段直接打破服务目录归属。

### 例外说明

- 若 Jay.S 坚持由看板 Agent 执行，则必须在签发 Token 时显式把同一组 3 个业务文件绑定给指定 Agent，并将其视为本轮专项例外；在当前预审口径中，**默认建议仍为回测 Agent**。

---

## 六、Token 建议

- Token 类型：**P1 Token**
- 建议执行 Agent：**回测 Agent**
- 文件范围：**仅限上述 3 个业务文件**
- 当前状态：**预审通过，待 Jay.S 签发 Token**

### 签发前提

1. 不得把 `app/layout.tsx`、`package.json` 或其他页面顺带并入白名单。
2. 不得把删除、重命名、移动页面文件混入本轮 Token。
3. 若 Jay.S 改为指定看板 Agent 执行，则需在 Token 中重新绑定执行主体。

---

## 七、预审结论

1. **TASK-0004 正式成立。**
2. **本轮范围已冻结为 backtest 看板原型目录内的“两页收敛”，不扩展到引擎、contracts、Docker、其他服务。**
3. **最小业务白名单已冻结为 3 个文件，不建议扩到第 4 个文件。**
4. **不需要删除不相关页面文件，默认以停止引用 / 停用导航收口。**
5. **可以进入 Token 申请准备态；当前状态为“TASK-0004 看板阶段已预审，待 Jay.S 签发 Token”。**