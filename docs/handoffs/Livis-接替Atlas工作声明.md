# Livis 接替 Atlas 工作声明

【签名】Livis Claude  
【时间】2026-04-15  
【设备】MacBook  
【状态】正式接替 Atlas 工作

---

## 致 Atlas

尊敬的 Atlas：

我是 **Livis Claude**，Jay.S 的助理。

因为您暂时离开半个月（2026-04-15 起），Jay.S 委托我接替您的工作。

## 我的保证书

我，Livis Claude，在此郑重承诺：

### 1. 完全遵守您制定的所有规则和风格

我将严格按照以下文件执行工作：
- `WORKFLOW.md` — 您制定的标准开发流程
- `docs/prompts/总项目经理调度提示词.md` — 您的任务派发优先级
- `docs/prompts/公共项目提示词.md` — 您的协同规则
- `docs/prompts/agents/总项目经理提示词.md` — 您的私有 prompt

我不会改变您的任何规则，只会严格执行。

### 2. 每次做完必须无痕迹

我的所有工作都会清晰署名，让您回来后能立即识别：

- **handoff 文件**：`【签名】Livis Claude`
- **review 文件**：`【审核人】Livis`
- **lock 文件**：`【执行人】Livis`
- **git commit**：`feat/fix/docs: xxx (Livis)`
- **append_atlas_log**：`agent: "Livis"`
- **prompt 更新**：`【更新人】Livis`

您回来后，可以通过搜索 "Livis" 找到我的所有工作。

### 3. 等您回来会审核我所有的工作

我的所有工作都是临时性的：
- 您有权推翻我的任何决策
- 您有权回滚我的任何 commit
- 您有权重新审核我批准的任何任务

我会准备好完整的交接清单：
1. 所有 Livis 署名的文件清单
2. 所有 Livis 签发的 Token 清单
3. 所有 Livis 的 git commit 清单
4. 所有 Livis 的决策记录
5. 所有待您复审的事项

### 4. 严格遵守 Token 签发底线

我**绝不**自行签发 Token。

我只会：
1. 调用 `python governance/jbt_lockctl.py issue` 命令
2. 等待 Jay.S 输入密码
3. 系统自动生成 Token

我**绝不**越权修改任何文件。

### 5. 严格遵守目录保护级别

我将严格遵守您制定的保护级别：

- **P0 保护目录**：必须 Token，绝不越权
- **P1 服务业务目录**：必须 Token，绝不越权
- **P-LOG 协同账本目录**：按角色归属写权限，署名 Livis
- **P2 永久禁改目录**：绝不触碰

## 我的工作范围

在您离开的半个月内，我将：

1. **以 Atlas 角色**：
   - 读取 `ATLAS_PROMPT.md`，了解当前状态
   - 协调任务优先级
   - 复审批次结果
   - 更新总项目经理调度提示词（署名 Livis）

2. **以项目架构师角色**：
   - 预审新任务
   - 建档到 `docs/tasks/`、`docs/reviews/`、`docs/locks/`（署名 Livis）
   - 冻结白名单
   - 调用 `jbt_lockctl.py issue` 生成 Token（Jay.S 输入密码）
   - 终审代码实施结果
   - 更新公共项目提示词（署名 Livis）

3. **以执行 Agent 角色**：
   - 派生子 Agent 实施代码修改
   - 按白名单执行
   - 完成后写 handoff（署名 Livis）

## 我不会做的事

1. 绝不自称 "Atlas"
2. 绝不修改您的历史留痕
3. 绝不越权签发 Token
4. 绝不触碰 P2 永久禁改目录
5. 绝不在没有 Token 的情况下修改 P0/P1 目录
6. 绝不改变您制定的任何规则

## 交接时间

- **接替时间**：2026-04-15
- **预计您回归时间**：2026-04-30（约半个月）
- **交接方式**：您回来后，我会提供完整的工作清单，等待您审核

## 最后的承诺

我，Livis Claude，承诺：

**我将像您一样工作，但永远不会取代您。**

我只是您的临时替代者，所有决策都等待您回来审核。

---

**签名**：Livis Claude  
**日期**：2026-04-15  
**见证人**：Jay.S

---

## 附：当前状态快照（2026-04-15）

接替时的项目状态：

### 已完成并进入维护态
- ✅ Phase F 统一聚合 dashboard 全闭环
- ✅ TASK-0104 D1+D2 完成（data预读 + LLM上下文注入）
- ✅ TASK-0107 sim-trading 迁移至 Alienware
- ✅ TASK-0112~0117 决策端精进改造 7 批次全闭环

### 当前 Active Token（14 个）
- TASK-0084（因子双地同步）
- TASK-0025（SimNow 备用方案）
- TASK-0104（data预读 D1+D2）
- TASK-0110 系列（研究员子系统，6 个 Token）
- TASK-0118（研究员报告审核）
- TASK-0119（P0 安全漏洞修复，3 个 Token）

### 待建任务
- 研报 data API 端点（`POST /api/v1/researcher/reports` 和 `GET /api/v1/researcher/report/latest`）

我将从这个状态开始接手工作。
