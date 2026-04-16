# Atlas → Claude 全量 Token 派工单（2026-04-15）【已更新 2026-04-15 下午】

> **使用规则**：按顺序逐一完成，完成一个汇报一个，等 Atlas 验收后再进入下一个。
> **当前状态**：TASK-0104 D1+D2 / TASK-0107 / TASK-0108 已全部收口完成。本文档转为存档用途，保留执行步骤与验收证据。

---

## 执行顺序（当前轮次）

```
Step 5（lockback） → Step 6（git push） → Step 7（两地同步）
```

步骤 1~4 均已完成，见下文存档。

---

---

## ✅ [已完成] 1. TASK-0104-D1 — data 侧预读系统（data 服务）

> **状态**：✅ 已验收锁回。commit `802c1f7`，token `tok-d8f23d88` locked。

### 原任务 — TASK-0104-D1

**Token**：`tok-d8f23d88-c183-45ba-8a59-8ad5700bfdb3`  
**Agent**：`Claude-Code`  
**有效期**：4320 min（~3天）

### check_token_access 参数（精确）
```json
{
  "task_id": "TASK-0104",
  "agent": "Claude-Code",
  "action": "write",
  "files": [
    "services/data/src/scheduler/data_scheduler.py",
    "services/data/src/scheduler/preread_generator.py",
    "services/data/src/api/routes/context_route.py",
    "services/data/src/main.py",
    "services/data/src/notify/dispatcher.py",
    "services/data/tests/test_preread.py"
  ]
}
```

### 白名单文件
| 文件 | 操作 |
|------|------|
| `services/data/src/scheduler/data_scheduler.py` | 修改 — 增加 21:00 夜间预读 job |
| `services/data/src/scheduler/preread_generator.py` | **新建** — 四角色摘要生成器 |
| `services/data/src/api/routes/context_route.py` | **新建** — GET /api/v1/context/daily |
| `services/data/src/main.py` | 修改 — 注册 context_route |
| `services/data/src/notify/dispatcher.py` | 修改 — 增加 PREREAD_DONE / PREREAD_FAIL |
| `services/data/tests/test_preread.py` | **新建** — 测试 |

### 核心要求
1. `preread_generator.py`：四角色摘要（researcher_context / l1_briefing / l2_audit_context / analyst_dataset），从已有 Collector 数据中聚合，覆盖 watchlist 30 只股票
2. `data_scheduler.py`：在 21:00 增加 job_nightly_preread()，参照现有 job 函数格式（_safe_run 包装）
3. `context_route.py`：暴露 `GET /api/v1/context/daily`，需要 API Key 认证（从已有 _verify_api_key 中间件）
4. `dispatcher.py`：新增 NotifyType.PREREAD_DONE / NotifyType.PREREAD_FAIL 两个枚举值
5. `main.py`：import context_route 并注册到 app

### 验收标准
- `pytest services/data/tests/test_preread.py -q` 全部通过
- `GET /api/v1/context/daily` 返回 HTTP 200，body 包含 4 个角色字段

---

## ✅ [已完成] 2. TASK-0104-D2 — decision 侧上下文注入（decision 服务）

> **状态**：✅ 已验收锁回。commit `d356511`，token `tok-6f298133` locked。6/6 测试通过（需 `.venv` 激活）。

### 原任务 — TASK-0104-D2

**Token**：`tok-6f298133-7364-44dd-a69c-1cebc10402e5`  
**Agent**：`Claude-Code`  
**前置**：TASK-0104-D1 验收通过后才能开始  
**有效期**：4320 min（~3天）

### check_token_access 参数（精确）
```json
{
  "task_id": "TASK-0104",
  "agent": "Claude-Code",
  "action": "write",
  "files": [
    "services/decision/src/llm/context_loader.py",
    "services/decision/src/llm/pipeline.py",
    "services/decision/src/llm/prompts.py",
    "services/decision/tests/test_llm_context.py"
  ]
}
```

### 白名单文件
| 文件 | 操作 |
|------|------|
| `services/decision/src/llm/context_loader.py` | **新建** — TTL=8h 内存缓存，HTTP pull from data API |
| `services/decision/src/llm/pipeline.py` | 修改 — 三角色方法注入上下文 |
| `services/decision/src/llm/prompts.py` | 修改 — 增加注释说明注入点 |
| `services/decision/tests/test_llm_context.py` | **新建** — 测试 |

### 核心要求
1. `context_loader.py`：`DATA_API_URL` 从 env 读取（默认 `http://localhost:8105`），TTL=8h，data 不可用时返回 None（降级，不中断 LLM 调用）
2. `pipeline.py`：research() 注入 researcher_context，audit() 注入 l2_audit_context+l1_briefing，analyze() 注入 analyst_dataset；ctx=None 时原有行为不变
3. `prompts.py`：只加注释，不改 prompt 文字内容

### 验收标准
- `pytest services/decision/tests/test_llm_context.py -q` 全部通过
- data API 不可用时 LLMPipeline.research() 无异常，正常返回

> 详细工单见 `docs/handoffs/TASK-0104-D2-工单-Claude.md`

---

## ✅ [已完成] 3. TASK-0107 — Alienware sim-trading 裸 Python 部署

> **状态**：✅ 已验收（Jay.S 确认）。`curl http://192.168.31.223:8101/health` → `{"status":"ok"}` ✅  
> 部署形式：**裸 Python**（非 Docker），`stage: 1.0.0`，`trading_enabled: true`，`active_preset: sim_50w`。  
> Token `tok-6c984fae` 已 lockback（approved）。

---

## ✅ [已完成] 4. TASK-0108 — MasterPlan 设备拓扑更新

> **状态**：✅ 代码层面完成。`docs/JBT_FINAL_MASTER_PLAN.md` 已含 [修订 2026-04-15] 全部 4 处改动：设备拓扑表（Alienware 含 sim-trading:8101，Mini 移除）、过渡注释、端口分配表（归属 Alienware）、§2.1 裸 Python 部署注脚。  
> Token `tok-5b749d0e` 已 lockback（approved）。

---

---

## 🔧 Step 5 — TASK-0107 & TASK-0108 Lockback（直接状态修改）

> **背景**：tok-6c984fae（TASK-0107）与 tok-5b749d0e（TASK-0108）的 JWT 原文未保存（.jbt 只存了 SHA256），CLI 无法 `--token` 锁回。Atlas 授权 Claude 使用以下 Python 脚本直接修改状态文件。  
> **文件不在 git 管理范围内**（.gitignore 已排除 `.jbt/**`）。
>
> **执行人**：Claude-Code

### 执行步骤

在 `/Users/jayshao/JBT` 目录运行：

```bash
cd /Users/jayshao/JBT && python3 - <<'EOF'
import json, time, os

STATE_DIR = "/Users/jayshao/JBT/.jbt/lockctl"
tokens_path = os.path.join(STATE_DIR, "tokens.json")
events_path = os.path.join(STATE_DIR, "events.jsonl")

LOCKBACK_TOKENS = [
    {
        "token_id": "tok-6c984fae-f518-4fdc-82c8-772e0601e598",
        "summary": "TASK-0107 验收通过：Alienware sim-trading 裸 Python 部署，curl /health → {status:ok}，stage:1.0.0，trading_enabled:true，active_preset:sim_50w [2026-04-15 Jay.S 确认]"
    },
    {
        "token_id": "tok-5b749d0e-b5fd-4bae-9da1-b63d05a7753a",
        "summary": "TASK-0108 验收通过：JBT_FINAL_MASTER_PLAN.md 设备拓扑 4 处全部更新 [修订 2026-04-15]，Alienware 行含 sim-trading:8101，Mini 行移除 sim-trading，端口表归属 Alienware [2026-04-15 Jay.S 确认]"
    },
]

with open(tokens_path) as f:
    data = json.load(f)

tokens = data["tokens"]
now = int(time.time())
new_events = []

for item in LOCKBACK_TOKENS:
    tid = item["token_id"]
    if tid not in tokens:
        print(f"❌ Token {tid} not found in tokens.json")
        continue
    entry = tokens[tid]
    if entry.get("status") != "active":
        print(f"⚠️  Token {tid} status={entry.get('status')}, skip")
        continue
    entry["status"] = "locked"
    entry["lockback_time"] = now
    entry["lockback_result"] = "approved"
    entry["lockback_summary"] = item["summary"]
    new_events.append(json.dumps({
        "event": "lockback",
        "time": now,
        "token_id": tid,
        "result": "approved",
        "summary": item["summary"]
    }, ensure_ascii=False))
    print(f"✅ {tid} → locked")

with open(tokens_path, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

with open(events_path, "a") as f:
    for line in new_events:
        f.write(line + "\n")

print("\n--- lockback 完成 ---")
EOF
```

### 验证命令
```bash
python3 governance/jbt_lockctl.py status 2>&1 | grep -E "tok-6c984fae|tok-5b749d0e"
```
期望输出：
```
tok-6c984fae-f518-4fdc-82c8-772e0601e598 | TASK-0107 | SimTrading | locked
tok-5b749d0e-b5fd-4bae-9da1-b63d05a7753a | TASK-0108 | Claude-Code | locked
```

---

## 🔧 Step 6 — git push & 两地同步

> **执行人**：Claude-Code  
> **前置**：Step 5 完成后才执行

### 6a. git push（MacBook → origin/main）

```bash
cd /Users/jayshao/JBT
git log --oneline -5
git push origin main
```

### 6b. Mini 同步（data 服务，D1 生效）

```bash
ssh jaybot@192.168.31.76 "cd ~/jbt && git pull && echo 'MINI PULL OK'"
```

> data scheduler 每日 21:00 自动触发 preread_generator，拉代码后隔天自动生效。

### 6c. Studio 同步（decision 服务，D2 生效）

```bash
ssh jaybot@192.168.31.142 "cd ~/jbt && git pull && echo 'STUDIO PULL OK'"
```

> decision 服务重启由 Jay.S 手动决定（生产服务），只做 git pull 即可。

### 验收标准
- `git push` 无 rejected，显示 `main -> main`
- Mini pull 显示 D1 文件已更新（preread_generator.py / context_route.py 等）
- Studio pull 显示 D2 文件已更新（context_loader.py / pipeline.py 等）

---

## Token 状态总览（全部收口 ✅）

| 任务 | Token ID | 状态 | 说明 |
|------|----------|------|------|
| TASK-0104-D1 | `tok-d8f23d88` | ✅ locked | commit 802c1f7，数据预读系统 |
| TASK-0104-D2 | `tok-6f298133` | ✅ locked | commit d356511，LLM 上下文注入 |
| TASK-0107 | `tok-6c984fae` | ✅ locked | Alienware 裸 Python 已运行，approved |
| TASK-0108 | `tok-5b749d0e` | ✅ locked | MasterPlan 4处已改，approved |

---

## 补充说明

1. **dashboard .env.local**：`services/dashboard/dashboard_web/.env.local` 已创建（git-ignored），`SIM_TRADING_URL=http://192.168.31.223:8101`。看板重启后立即生效，无需 token（runtime 配置文件）。
2. **pytest 注意**：decision 服务测试必须先 `source /Users/jayshao/JBT/.venv/bin/activate` 才能找到 pytest-asyncio。
3. **TASK-0107 部署口径**：裸 Python（非 Docker），`active_preset: sim_50w`，当前连 SimNow（非光大期货生产）。Docker 化部署待 Alienware BIOS 虚拟化开启后另行建任务。

---

**创建时间**：2026-04-15  
**签发人**：Atlas  
**最后更新**：2026-04-15（Step 5~6 收口轮次）
