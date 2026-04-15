# TASK-0119 预审记录

【预审人】项目架构师（Livis）  
【日期】2026-04-15  
【状态】预审通过

---

## 1. 服务边界确认

- ✅ 仅涉及 `services/data/` 与 `services/decision/`
- ✅ 不触及 `shared/contracts/**`
- ✅ 不触及 `shared/python-common/**`
- ✅ 不触及 `WORKFLOW.md` 与 `.github/**`

## 2. 白名单核查

本次总 Token 白名单共 16 个文件，范围与 [docs/handoffs/TASK-0119-Claude-安全漏洞修复派工单.md](docs/handoffs/TASK-0119-Claude-安全漏洞修复派工单.md) 一致，允许一次性签发。

## 3. 风险评估

| 风险 | 级别 | 处理 |
|------|------|------|
| 认证/注入修复影响既有请求路径 | P1 | 需配套新增安全测试与最小回归测试 |
| decision/data 双服务同时改动 | P1 | 批次化执行并分别验证 |
| 安全修复引入新的行为回归 | P1 | 以测试结果与风控报告修复项双重验证 |

## 4. 预审结论

**批准通过。** 允许 Atlas 为 Claude 以一次性总 Token 方式签发 16 文件白名单。实施完成后必须补充 lockback 与最终审计留痕。
# TASK-0119 预审记录

【预审】项目架构师  
【日期】2026-04-15  
【状态】通过

## 审核意见

本次修复基于 2026-04-15 风控常规体检报告，覆盖 4 个 P0 高危漏洞、7 个 P1 中危漏洞，修复方案合理，服务边界清晰：

- 批次 A：data 服务认证/命令注入/信息泄露 — P0，紧急
- 批次 B：decision 服务 Prompt 注入/内存泄漏/HTML 注入/文件权限 — P0+P1，高优先
- 批次 C：爬虫 XPath 注入/异常处理/输入验证 — P1+P2，中优先
- 批次 D：通用安全增强（超时/速率限制/并发/审计） — P2，低优先

## 文件白名单确认

已核查，全部 16 个文件均在对应服务目录内，无跨服务越界：

### data 服务（9 个文件）
- `services/data/src/main.py`
- `services/data/src/notify/card_templates.py`
- `services/data/src/collectors/tushare_full_collector.py`
- `services/data/tests/test_main.py`
- `services/data/tests/test_security.py`
- `services/data/src/researcher/crawler/parsers/futures.py`
- `services/data/src/researcher/scheduler.py`

### decision 服务（9 个文件）
- `services/decision/src/llm/gate_reviewer.py`
- `services/decision/src/core/signal_dispatcher.py`
- `services/decision/src/notifier/email.py`
- `services/decision/src/persistence/state_store.py`
- `services/decision/tests/test_llm_security.py`
- `services/decision/tests/test_signal_dispatcher.py`
- `services/decision/src/research/factor_loader.py`
- `services/decision/src/api/app.py`
- `services/decision/src/research/sandbox_engine.py`

## 结论

预审通过，白名单已冻结，可签发 Token。
