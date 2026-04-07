# TASK-0021 D 批 — 研究中心实现交接单

**交接方**：决策 Agent  
**接收方**：项目架构师（Atlas）终审  
**日期**：2026-04-07  
**Token**：tok-17b4655f-48e1-4cf6-9196-95bc4d669747  

---

## 1. 本批完成内容

### 新增文件（11 个白名单文件全部落地）

| 文件 | 说明 |
|---|---|
| `services/decision/src/gating/backtest_gate.py` | BacktestGate：内存存储回测证书，is_valid / register_cert / invalidate / get_cert |
| `services/decision/src/gating/research_gate.py` | ResearchGate：内存存储研究快照，is_complete / register_snapshot / get_snapshot |
| `services/decision/src/research/__init__.py` | 懒加载聚合层（__getattr__），TYPE_CHECKING 导出 6 个核心类 |
| `services/decision/src/research/session.py` | ResearchSession + ResearchArtifacts，4 状态机（pending/running/completed/failed） |
| `services/decision/src/research/trainer.py` | XGBoostTrainer：train / cross_validate，顶层 `import xgboost as xgb` |
| `services/decision/src/research/optuna_search.py` | OptunaSearch：run_search，n_estimators/max_depth/learning_rate/subsample 搜索空间 |
| `services/decision/src/research/shap_audit.py` | ShapAuditor：explain / save_summary，TreeExplainer + JSON 摘要 |
| `services/decision/src/research/onnx_export.py` | OnnxExporter：export（onnxmltools + onnxruntime 验证推理） |
| `services/decision/src/research/factor_loader.py` | FactorLoader：load（mock numpy 数组） + compute_hash（SHA-256） |
| `services/decision/tests/test_gating.py` | 9 个用例（BacktestGate / ResearchGate / 过期逻辑） |
| `services/decision/tests/test_research.py` | 12 个用例（SessionState / FactorLoader / XGBoost ImportError / Optuna ImportError） |

---

## 2. get_errors 结果

**全部 11 文件 + __init__.py：0 errors。**

- `xgboost` / `optuna` / `onnxruntime` / `onnxmltools` 未安装，顶层 import 加 `# type: ignore` 消除 pylance 误报；运行时 ImportError 仍正常传播（不吞错）。
- `shap` 未安装但 pylance 无误报（推测有残留 stub）。

---

## 3. 测试汇总

```
测试运行：21 passed in 0.24s
- test_gating.py：9 个用例（全通过）
  - test_backtest_gate_register_and_valid
  - test_backtest_gate_unknown_strategy
  - test_backtest_gate_invalidate
  - test_cert_expiry（expires_days=-1 → is_valid=False → status=expired）
  - test_cert_get_cert_returns_none_for_unknown
  - test_research_gate_register_and_complete
  - test_research_gate_unknown_strategy
  - test_research_gate_snapshot_fields
  - test_research_gate_get_snapshot

- test_research.py：12 个用例（全通过）
  - test_research_session_init
  - test_research_session_start
  - test_research_session_complete
  - test_research_session_fail
  - test_research_session_invalid_transition
  - test_research_session_complete_invalid
  - test_research_session_artifacts_default
  - test_factor_loader_compute_hash_deterministic
  - test_factor_loader_compute_hash_distinct
  - test_factor_loader_mock_load
  - test_xgboost_trainer_import_error（sys.modules mock）
  - test_optuna_search_import_error（sys.modules mock）
```

---

## 4. 关键实现决策

### 4.1 BacktestGate 存储设计
- 内存 dict：`strategy_id → BacktestCert`（每策略只保留最新一张证书）
- 字段名对齐契约：`certificate_id`（not `cert_id`），`review_status`（not `status`）
- 枚举对齐契约：`pending/approved/rejected/expired`（task 描述中的 `valid/invalid` 已纠正为契约值）
- 过期检测惰性刷新：`_refresh_expiry()` 在 `is_valid` / `get_cert` 时自动将过期 approved 证书切换为 expired

### 4.2 ResearchGate 存储设计
- 内存 dict：`strategy_id → ResearchSnapshot`
- 字段名对齐契约：`research_snapshot_id`（≠ `session_id`），`factor_version_hash`（≠ `factor_hash`）
- 方法参数使用缩写（`session_id`, `factor_hash`），内部映射到契约字段名

### 4.3 XGBoostTrainer 接口
- `train(X, y, params) → xgb.XGBClassifier`
- `cross_validate(X, y, params, cv=5) → dict[str, float]`（sharpe/drawdown/accuracy，以 accuracy 代理 sharpe，生产阶段替换）
- LightGBM / CatBoost adapter 注释预留位

### 4.4 research/__init__.py 懒加载
- 背景：test_research.py 需"不依赖 xgboost/optuna/shap/onnx"，但 session.py / factor_loader.py 在同一 package 内
- 方案：`__init__.py` 改用 `__getattr__` 懒加载，个别模块文件保留顶层 import
- 效果：`from src.research.session import ResearchSession` 不触发 xgboost/onnx 加载；`from src.research import XGBoostTrainer` 仅在访问时触发

---

## 5. 接口核对（与 C 批一致性）

- `ModelRouter`（C 批）接受 `backtest_certificate_id` / `research_snapshot_id` 字符串参数，不直接调用 `BacktestGate.is_valid()`。D 批 Gate 类与 Router 间无强耦合，接口兼容。
- `StrategyLifecycle.backtest_confirmed` 状态与 `BacktestGate.is_valid()` 语义对齐（均表示回测已通过）。

---

## 6. 遗留事项（需 E 批或后续批次处理）

1. `ModelRouter` 目前只检查 `backtest_certificate_id` 字符串是否为 None，未调用 `BacktestGate.is_valid()`。E 批可注入 Gate 实例做真实校验。
2. `FactorLoader.load()` 为 mock 实现，data service 就绪后替换真实 HTTP 调用。
3. `OnnxExporter` / `ShapAuditor` 依赖 onnxmltools / shap，需在 pyproject.toml 补充可选依赖（架构师负责契约变更后，由 Jay.S 解锁 pyproject.toml 修改权限）。

---

## 7. 锁控要求

本批量创建的文件均为**新建**，无需 lockback（新建文件不在锁控范围内）。  
若后续 E 批需修改本批文件，需重新申请 Token。

---

**决策 Agent 自校验**：11 文件 0 errors，21 测试 0 failures。交接完毕，等待项目架构师终审。
