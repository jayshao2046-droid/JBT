# TASK-0024 — JBT 全平台部署就绪审查报告

【签名】Atlas
【时间】2026-04-08
【设备】MacBook
【性质】代码审查 + 最小 P2 修复

---

## 一、修正后部署架构（Jay.S 确认口径）

| 服务 | API 端口 | 临时看板端口 | 部署位置 | 备注 |
|------|:---:|:---:|:---:|------|
| **sim-trading** | 8101 | 3002 (sim-trading_web) | Mini | 容器常驻，蒲公英访问 |
| **decision** | 8104 | 3003 (decision_web) | 本地→Studio | 看板未通过验收，暂搁 |
| **backtest** | 8103 | 3001 (backtest_web) | Air | 已部署运行 |
| **data** | 8105 | — | Mini Docker | 已连通已在用 |
| **dashboard** | 8106 | — | — | **待开发**，不影响当前 |
| **live-trading** | 8102 | — | — | **待开发**，不影响当前 |

**架构关键约束（Jay.S 确认）：**
1. 聚合看板(dashboard)待开发，各服务用自己容器内的临时看板
2. 模拟交易部署在 Mini 容器，只需与 Mini 的决策端 API 连接
3. 不需要连接模拟看板，只通过后端 API 互联
4. 决策端不连回测端，所有回测在决策端内部进行
5. data 数据在 Mini Docker 容器，已通过回测端连通并在使用
6. Mini 通过蒲公英(172.16.0.49)连接，部署到 Studio 后改内网

---

## 二、服务部署就绪矩阵

| 服务 | Docker 可构建 | 容器可启动 | 测试通过 | 临时看板连通 | 部署状态 |
|------|:---:|:---:|:---:|:---:|:---:|
| **decision** (8104) | ✅ | ✅ | 95/95 ✅ | 待验收 | **可部署** |
| **decision_web** (3003) | ✅ | ✅ | — | ✅ rewrites OK | **可构建**（未验收） |
| **sim-trading** (8101) | ✅ | ✅ | 19/19+1skip ✅ | — | **已部署 Mini** |
| **sim-trading_web** (3002) | ✅ | ✅ | — | ✅ Mini 200 | **已部署 Mini** |
| **backtest** (8103) | ✅ | ✅ | 50/52 ⚠️ | — | **已部署 Air** |
| **backtest_web** (3001) | ✅ | ✅ | — | ✅ Air 运行 | **已部署 Air** |
| **data** (8105) | ✅ (Mini) | ✅ | — | — | **已部署 Mini** |
| **dashboard** (8106) | — | — | — | — | **待开发** |
| **live-trading** (8102) | — | — | — | — | **待开发** |

---

## 三、跨服务 API 连通性

| 调用链 | 状态 | 说明 |
|--------|:---:|------|
| decision → sim-trading `/api/v1/strategy/publish` | ✅ | `sim_adapter.py` 正确处理 202 Accepted |
| decision → data `/api/v1/bars` | ✅ | `factor_loader.py` 已接入，timeout 已改为可配置 |
| decision_web → decision (rewrites) | ✅ | `next.config.mjs` rewrites `/api/decision/*` → `:8104` |
| sim-trading_web → sim-trading | ✅ | Mini 同主机，蒲公英 200 |
| backtest → data (Mini PGY/Tailscale) | ✅ | 已连通在用 |
| backtest_web → backtest | ✅ | Docker 服务名 `backtest:8103` |

---

## 四、Mini Data API 验证结果

- 蒲公英: 172.16.0.49:8105 ✅ ping 38~43ms
- `/health` → `{"status":"ok","service":"data","version":"0.1.0-minimal"}`
- `/api/v1/symbols` → 260 symbols（5 交易所 + 63 主力连续合约）
  - CFFEX: 20, CZCE: 52, DCE: 62, GFEX: 10, INE: 12, SHFE: 41, KQ: 63
- `/api/v1/bars` → KQ_m_DCE_p 2026-04-01~04-03 返回 915 bars ✅

---

## 五、Bug 清单（修正后）

### P0 — 部署阻断

| # | 说明 | 状态 |
|---|------|:---:|
| ~~P0-1~~ | dashboard 后端空白 | Jay.S 确认：**待开发**，不是代码丢失 |
| ~~P0-2~~ | data 无 Dockerfile | Jay.S 确认：data 在 Mini Docker **已部署已在用** |
| P0-3 | 根目录 `.env` 含明文凭据未加 `.gitignore` | ✅ 已加入 `.gitignore`（`.env` + `.env.*` + `!.env.example`） |

### P1 — 功能缺陷

| # | 说明 | 状态 |
|---|------|:---:|
| P1-1 | decision `signal.py` `_decisions` 进程局部 | **影响范围有限**：仅"历史审批结果查询"丢失，核心策略状态/审批/回测证书/研究快照已通过 FileStateStore 持久化 |
| P1-2 | sim-trading `execution/service.py` NotImplementedError | Jay.S 确认：后续完成模拟交易后再调试，**记录** |
| P1-3 | sim-trading `ledger/service.py` NotImplementedError | 同上，**记录** |
| P1-4 | sim-trading `risk/guards.py` NotImplementedError | 同上，**记录** |
| P1-5 | backtest 2 个测试失败 | Jay.S 确认：回测只做人工手动回测，决策端内部回测不依赖回测端，**记录** |

### P2 — 次要问题（本轮已修复 ✅）

| # | 说明 | 状态 |
|---|------|:---:|
| P2-1 | decision `health.py` 端口硬编码 | ✅ 已改为读 `settings.decision_port` |
| P2-2 | decision `gate.py` archived 双重检查 | **设计合理**：step2 提供显式拒绝消息，step3 做状态转移验证，各有目的 |
| P2-3 | decision `factor_loader.py` timeout 硬编码 | ✅ 已改为读 `settings.data_service_timeout`（默认 30s） |
| P2-4 | decision 缺 `/strategies/{id}/retire` 路由 | **后续功能**，不阻塞当前部署 |
| P2-5 | decision 缺请求追踪中间件 | **后续功能**，不阻塞当前部署 |

### P2 修复文件

- `services/decision/src/api/routes/health.py` — 导入 settings，端口从配置读取
- `services/decision/src/core/settings.py` — 新增 `data_service_timeout: int = 30`
- `services/decision/src/research/factor_loader.py` — 移除 `_API_TIMEOUT_SECONDS`，改读 settings
- `services/decision/tests/test_research.py` — 更新 timeout 断言为 30

---

## 六、待办记录

### P0-3: .env 安全 ✅ 已修复
- 根目录 `.env` 含 SIMNOW 凭据、SMTP 密码
- `.gitignore` 已补充 `.env` / `.env.*` / `!.env.example` 三规则
- 验证：`git check-ignore .env` → 已忽略；`.env.example` → 不忽略
- `.env` 确认从未被 git 追踪（`git ls-files --error-unmatch .env` → not tracked）

### 决策端 SimNow 备用方案 ✅ 已建档
- 已建档为 `TASK-0025-decision-SimNow备用方案-仅平仓模式`
- 需求：模拟交易端离线时，决策端启动备用直连 SimNow，仅可平仓
- 初步拆批：A(连通性检测+状态机) → B(CTP直连+仅平仓) → C(恢复检测+通知)
- 前置条件：TASK-0021 decision 基础闭环 + TASK-0023-A 发布接口对接

### sim-trading_web Linux 兼容
- `docker-compose.dev.yml` 中 `BACKEND_BASE_URL: http://host.docker.internal:8101` 仅 macOS 生效
- Mini 部署已正常（用户确认 200 OK），但标准做法应改用 Docker 服务名或 extra_hosts
- 状态：**当前不阻塞**，部署到 Studio 时需确认

---

## 七、自校验

- decision 全量测试：95 passed ✅
- Mini data API: 260 symbols, bars 正常 ✅
- Mini sim-trading: health OK ✅
- Mini sim-trading_web: HTTP 200 ✅
- P2 修复后无回归 ✅
