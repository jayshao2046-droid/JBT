# TASK-0021 C0 批 — 决策服务 .env.example 环境模板完善 交接单

【签名】决策 Agent  
【交接时间】2026-04-07  
【review_id】REVIEW-TASK-0021-C0  
【token_id】tok-79cc37ff-b255-457d-aa20-085699e2c923  

---

## 执行结果摘要

**状态：已完成，待项目架构师终审与 lockback**

---

## 变更文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/.env.example` | 全量覆盖重写 | 旧 8 行骨架 → 13 分组标准模板 |
| `docs/prompts/agents/决策提示词.md` | 更新 | 同步状态、动作日志、下一步 |

---

## .env.example 分组概览（13 组）

| # | 分组 | 关键变量 |
|---|------|---------|
| 1 | 基础服务配置 | `DECISION_HOST`, `DECISION_PORT=8104`, `DECISION_WORKERS`, `DECISION_ENV` |
| 2 | 研究窗口配置 | `RESEARCH_WINDOW_START/END`, `RESEARCH_TIMEZONE`, `OVERNIGHT_RESEARCH_ENABLED` |
| 3 | 本地模型配置 | `LOCAL_MODEL_MAIN=Qwen3-14B`, `LOCAL_MODEL_COMPAT=DeepSeek-R1-14B`, `LOCAL_MODEL_L1=Qwen2.5`, Ollama URL |
| 4 | 在线模型配置 | `ONLINE_MODEL_DEFAULT=Qwen3.6-Plus`, `UPGRADE=Qwen3-Max`, `BACKUP=DeepSeek-V3.2`, `DISPUTE=DeepSeek-R1` |
| 5 | XGBoost 研究 | `XGBOOST_ENABLED=true`, N_ESTIMATORS/MAX_DEPTH/LEARNING_RATE |
| 6 | LightGBM 占位 | `LIGHTGBM_ENABLED=false`（保留抽象位） |
| 7 | CatBoost 占位 | `CATBOOST_ENABLED=false`（保留抽象位） |
| 8 | ONNX Runtime | `ONNX_RUNTIME_ENABLED=true`, INFERENCE_THREADS=2 |
| 9 | Optuna 参数搜索 | `OPTUNA_ENABLED=true`, sqlite 存储, N_TRIALS=100 |
| 10 | SHAP 解释审计 | `SHAP_ENABLED=true`, AUDIT_DIR, MAX_DISPLAY=20 |
| 11 | 执行门禁 | `EXECUTION_GATE_TARGET=sim-trading`, `LIVE_TRADING_GATE_LOCKED=true` |
| 12 | 模型路由门禁 | `REQUIRE_BACKTEST_CERT=true`, `MIN_SHARPE=0.5`, `MAX_DRAWDOWN=0.20` |
| 13 | 回测/数据服务集成、通知、日报、数据库 | localhost 端口默认值；飞书/邮件默认关闭；sqlite 占位 |

---

## 校验结果

```
get_errors: 0 errors
```

---

## 设计决策说明

1. **端口统一**：`DECISION_PORT=8104` 与 `shared/contracts/README.md` 及 PORT_REGISTRY 保持一致。
2. **执行门禁**：`live-trading` 可见但锁定（`LIVE_TRADING_GATE_LOCKED=true`），与 A 批契约冻结的第一阶段发布策略对齐。
3. **模型配置独立分组**：本地与在线分离，便于生产环境只注入 `ONLINE_MODEL_API_KEY`。
4. **LightGBM / CatBoost**：默认关闭，保留抽象位，保持与 A 批契约中"研究主线 XGBoost"的一致性。
5. **通知默认关闭**：`FEISHU_ENABLED=false` / `EMAIL_ENABLED=false`，防止模板文件泄漏 webhook。

---

## 后续要求（给项目架构师）

1. 对本批次（1 文件）完成终审（REVIEW-TASK-0021-C0）。
2. 终审通过后执行 lockback：
   ```
   python governance/jbt_lockctl.py lockback \
     --token "<C0-JWT>" \
     --result approved \
     --review-id REVIEW-TASK-0021-C0 \
     --summary "TASK-0021 C0 批 .env.example 完善终审通过，1文件0errors，13分组完整，执行锁回"
   ```
