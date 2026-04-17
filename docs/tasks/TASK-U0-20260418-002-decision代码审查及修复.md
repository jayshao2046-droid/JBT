# TASK-U0-20260418-002 decision 代码审查及修复

【签名】Atlas  
【时间】2026-04-18  
【状态】A0 建档完成，等待项目架构师预审

---

## 1. 任务概述

**目标**：对 Studio decision 服务进行全面代码审查，修复发现的 17 处问题（3 个严重漏洞 + 6 个中等问题 + 8 个代码质量问题）。

**触发原因**：Jay.S 指令"检查 Studio decision 所有代码，检查 bug 代码错误及漏洞"，已完成只读诊断并发现 17 处问题。

**范围**：`services/decision/src/` 下所有 Python 代码（121 个文件）

**优先级**：U0（紧急修复）

---

## 2. 问题清单（按严重程度）

### 🔴 P0 严重漏洞（3 个）

#### P0-1: 代码注入风险 - yaml_signal_executor.py
- **文件**：`services/decision/src/research/yaml_signal_executor.py`
- **问题**：使用 `exec()` 执行 LLM 生成的代码，虽然有 `safe_globals` 限制，但仍存在沙箱逃逸风险
- **代码位置**：
  ```python
  exec(compile(code, "<generated_signal>", "exec"), safe_globals, local_ns)  # noqa: S102
  ```
- **风险**：
  - LLM 生成的恶意代码可能绕过沙箱限制
  - `_SAFE_BUILTINS` 包含 `Exception` 等可能被滥用的类
  - 虽然禁止了 `import`，但可能通过内置函数访问危险对象
- **修复方案**：
  1. 使用 AST 白名单验证生成的代码，只允许特定的语法结构
  2. 添加执行超时和资源限制（CPU、内存）
  3. 考虑使用独立进程沙箱（如 RestrictedPython）
  4. 添加代码审计日志，记录所有执行的生成代码

#### P0-2: Prompt 注入防护不完整 - gate_reviewer.py
- **文件**：`services/decision/src/llm/gate_reviewer.py`
- **问题**：`_sanitize_context()` 的正则过滤可以被绕过
- **代码位置**：
  ```python
  dangerous_patterns = [
      r'(?i)ignore\s+(all\s+)?(previous\s+)?(instructions?|prompts?|rules?)',
      # ...
  ]
  ```
- **风险**：
  - 攻击者可以使用变体绕过正则（如 "ign0re previous instructions"）
  - 仅限制 2000 字符不足以防止所有注入
  - 没有检测 Unicode 混淆、零宽字符等高级技巧
- **修复方案**：
  1. 使用更严格的输入验证，只允许预期的数据格式
  2. 对 LLM 输入使用结构化格式（JSON schema）而非自由文本
  3. 添加输出验证，检测 LLM 响应是否包含异常内容
  4. 实施速率限制和异常检测

#### P0-3: 文件权限竞态 - state_store.py
- **文件**：`services/decision/src/persistence/state_store.py`
- **问题**：虽然已设置 `chmod(0o600)`，但在多用户环境下仍有风险
- **代码位置**：
  ```python
  tmp_path.chmod(0o600)
  tmp_path.replace(self._file_path)
  self._file_path.chmod(0o600)
  ```
- **风险**：
  - 在 `replace()` 之前的短暂时间窗口，文件可能被其他进程访问
  - 没有验证父目录权限
  - 锁文件 `.lock` 没有设置权限
- **修复方案**：
  1. 使用 `os.open()` 配合 `O_CREAT | O_EXCL` 原子创建文件
  2. 验证父目录权限（应为 700）
  3. 对锁文件也设置严格权限
  4. 考虑使用加密存储敏感数据

### 🟡 P1 中等问题（6 个）

#### P1-1: 内存泄漏风险 - signal_dispatcher.py
- **文件**：`services/decision/src/core/signal_dispatcher.py`
- **问题**：`_dispatched` 字典无限增长，虽然有 `max_history` 限制但淘汰逻辑效率低
- **修复方案**：使用 `collections.OrderedDict` 并添加线程锁，或使用 LRU 缓存

#### P1-2: TOCTOU 竞态条件 - sandbox_engine.py
- **文件**：`services/decision/src/research/sandbox_engine.py`
- **问题**：缓存检查和写入不是原子操作
- **修复方案**：添加缓存 TTL 机制，确保所有共享状态都有适当的并发控制

#### P1-3: 异常处理不当 - 多个文件
- **问题**：裸 `except Exception` 吞掉所有错误，难以调试
- **修复方案**：使用具体的异常类型，保留 `KeyboardInterrupt` 和 `SystemExit` 不捕获

#### P1-4: 资源泄漏 - OllamaClient
- **文件**：`services/decision/src/llm/client.py`
- **问题**：`httpx.AsyncClient` 没有自动关闭机制
- **修复方案**：使用上下文管理器或在 `__del__` 中关闭

#### P1-5: 无边界检查 - sandbox_engine.py
- **文件**：`services/decision/src/research/sandbox_engine.py`
- **问题**：数组访问前没有充分验证
- **修复方案**：添加参数范围验证，使用 `max(0, i - short_window)` 防止负索引

#### P1-6: 日志泄露敏感信息 - gate_reviewer.py
- **文件**：`services/decision/src/llm/gate_reviewer.py`
- **问题**：返回的前 200 字符可能包含敏感信息
- **修复方案**：完全移除原始响应内容，只返回错误类型

### 🔵 P2 代码质量（8 个）

- P2-1: 硬编码配置 - 多个文件
- P2-2: 重复代码 - context_loader.py
- P2-3: 缺少类型注解 - 部分函数
- P2-4: 过长函数 - yaml_signal_executor.py
- P2-5: 缺少并发保护 - sandbox_engine.py
- P2-6: 魔法字符串 - 多处
- P2-7: 缺少输入验证 - API 路由
- P2-8: 测试覆盖不足

---

## 3. 批次规划

### 批次 A1：P0 严重漏洞修复（优先）

**文件清单**（3 个文件）：
1. `services/decision/src/research/yaml_signal_executor.py` - P0-1 代码注入
2. `services/decision/src/llm/gate_reviewer.py` - P0-2 Prompt 注入
3. `services/decision/src/persistence/state_store.py` - P0-3 文件权限

**修复内容**：
- yaml_signal_executor.py：添加 AST 白名单验证、执行超时、资源限制、审计日志
- gate_reviewer.py：增强输入验证、使用结构化格式、添加输出验证、速率限制
- state_store.py：使用 `os.open()` 原子创建、验证父目录权限、锁文件权限

**验收标准**：
- [ ] AST 白名单能拒绝危险语法（`import`、`eval`、`exec`、`__import__`）
- [ ] 执行超时能在 5 秒内终止恶意代码
- [ ] Prompt 注入测试用例全部通过（Unicode 混淆、零宽字符、变体绕过）
- [ ] 文件权限在所有操作中保持 0o600
- [ ] 锁文件权限为 0o600

### 批次 A2：P1 中等问题修复（不含异常处理）

**文件清单**（3 个文件 + 3 个测试文件）：
1. `services/decision/src/core/signal_dispatcher.py` - P1-1 内存泄漏
2. `services/decision/src/research/sandbox_engine.py` - P1-2 竞态条件 + P1-5 边界检查
3. `services/decision/src/llm/client.py` - P1-4 资源泄漏
4. `services/decision/tests/test_signal_dispatcher.py` - 测试用例
5. `services/decision/tests/test_sandbox_engine.py` - 测试用例
6. `services/decision/tests/test_client.py` - 测试用例

**修复内容**：
- signal_dispatcher.py：使用 `cachetools.LRUCache`（线程安全、自动淘汰）
- sandbox_engine.py：添加缓存 TTL（5 分钟）、参数范围验证、防止负索引
- client.py：添加 `async with` 上下文管理器

**验收标准**：
- [ ] `_dispatched` 字典大小不超过 `max_history`
- [ ] 缓存有 TTL 机制，过期自动清理
- [ ] 数组访问前有范围验证，不会抛出 `IndexError`
- [ ] `httpx.AsyncClient` 在服务停止时正确关闭

### 批次 A2-EX：P1-3 异常处理专项修复

**背景**：扫描发现 92 处 `except Exception`，涉及 39 个文件，数量较多，单独建批次。

**文件清单**（39 个文件）：
```
services/decision/src/api/routes/factor.py
services/decision/src/api/routes/local_sim.py
services/decision/src/api/routes/pbo.py
services/decision/src/api/routes/researcher_evaluate.py
services/decision/src/api/routes/strategy_import.py
services/decision/src/llm/client.py
services/decision/src/llm/context_loader.py
services/decision/src/llm/online_confirmer.py
services/decision/src/llm/openai_client.py
services/decision/src/llm/pipeline.py
services/decision/src/llm/researcher_loader.py
services/decision/src/llm/researcher_phi4_scorer.py
services/decision/src/llm/researcher_scorer.py
services/decision/src/notifier/email.py
services/decision/src/notifier/feishu.py
services/decision/src/notifier/health_monitor.py
services/decision/src/publish/executor.py
services/decision/src/publish/failover.py
services/decision/src/publish/sim_adapter.py
services/decision/src/reporting/daily.py
services/decision/src/research/code_generator.py
services/decision/src/research/context_compressor.py
services/decision/src/research/factor_loader.py
services/decision/src/research/feature_cache_manager.py
services/decision/src/research/meta_optimizer.py
services/decision/src/research/model_registry.py
services/decision/src/research/news_scorer.py
services/decision/src/research/optimization_data_collector.py
services/decision/src/research/param_mapping_applicator.py
services/decision/src/research/regime_detector.py
services/decision/src/research/sandbox_engine.py
services/decision/src/research/spread_monitor.py
services/decision/src/research/stock_screener.py
services/decision/src/research/strategy_architect.py
services/decision/src/research/strategy_evaluator.py
services/decision/src/research/symbol_profiler.py
services/decision/src/research/three_tier_optimizer.py
services/decision/src/research/trade_optimizer.py
services/decision/src/research/yaml_signal_executor.py
services/decision/src/stats/optimizer.py
```

**修复内容**：
- 将 `except Exception` 改为具体异常类型（`httpx.HTTPError`、`ValueError`、`KeyError` 等）
- 在 `except Exception` 前先 `except (KeyboardInterrupt, SystemExit): raise`
- 添加 `exc_info=True` 记录完整堆栈

**验收标准**：
- [ ] 所有 `except Exception` 前都有 `except (KeyboardInterrupt, SystemExit): raise`
- [ ] 关键路径使用具体异常类型（至少 50% 以上）
- [ ] 所有异常日志包含 `exc_info=True`

### 批次 A3：P2 代码质量改进

**文件清单**（多个文件，按需选择）：
1. 配置文件提取（硬编码 → 环境变量/配置文件）
2. 重复代码提取（context_loader.py）
3. 类型注解补充（部分函数）
4. 长函数拆分（yaml_signal_executor.py）
5. 魔法字符串枚举化
6. 输入验证增强（API 路由）
7. 测试覆盖补充

**修复内容**：
- 提取硬编码配置到 `settings.py` 或环境变量
- 提取 L1/L2 上下文加载公共函数
- 添加类型注解，使用 `mypy` 静态检查
- 拆分 `execute()` 函数为多个小函数
- 使用 `enum.Enum` 替代魔法字符串
- 使用 Pydantic `validator` 添加输入验证
- 补充单元测试

**验收标准**：
- [ ] 所有硬编码配置移至 `settings.py` 或环境变量
- [ ] 重复代码减少 50% 以上
- [ ] 所有公共函数有类型注解
- [ ] 单个函数不超过 100 行
- [ ] 魔法字符串全部枚举化
- [ ] API 路由有输入验证
- [ ] 测试覆盖率 > 80%

---

## 4. 文件级白名单

### A1 白名单（6 个文件：3 源码 + 3 测试）
```
services/decision/src/research/yaml_signal_executor.py
services/decision/src/llm/gate_reviewer.py
services/decision/src/persistence/state_store.py
services/decision/tests/test_yaml_signal_executor_security.py
services/decision/tests/test_gate_reviewer_security.py
services/decision/tests/test_state_store_security.py
```

### A2 白名单（6 个文件：3 源码 + 3 测试）
```
services/decision/src/core/signal_dispatcher.py
services/decision/src/research/sandbox_engine.py
services/decision/src/llm/client.py
services/decision/tests/test_signal_dispatcher.py
services/decision/tests/test_sandbox_engine.py
services/decision/tests/test_client.py
```

### A2-EX 白名单（39 个文件）
```
services/decision/src/api/routes/factor.py
services/decision/src/api/routes/local_sim.py
services/decision/src/api/routes/pbo.py
services/decision/src/api/routes/researcher_evaluate.py
services/decision/src/api/routes/strategy_import.py
services/decision/src/llm/client.py
services/decision/src/llm/context_loader.py
services/decision/src/llm/online_confirmer.py
services/decision/src/llm/openai_client.py
services/decision/src/llm/pipeline.py
services/decision/src/llm/researcher_loader.py
services/decision/src/llm/researcher_phi4_scorer.py
services/decision/src/llm/researcher_scorer.py
services/decision/src/notifier/email.py
services/decision/src/notifier/feishu.py
services/decision/src/notifier/health_monitor.py
services/decision/src/publish/executor.py
services/decision/src/publish/failover.py
services/decision/src/publish/sim_adapter.py
services/decision/src/reporting/daily.py
services/decision/src/research/code_generator.py
services/decision/src/research/context_compressor.py
services/decision/src/research/factor_loader.py
services/decision/src/research/feature_cache_manager.py
services/decision/src/research/meta_optimizer.py
services/decision/src/research/model_registry.py
services/decision/src/research/news_scorer.py
services/decision/src/research/optimization_data_collector.py
services/decision/src/research/param_mapping_applicator.py
services/decision/src/research/regime_detector.py
services/decision/src/research/sandbox_engine.py
services/decision/src/research/spread_monitor.py
services/decision/src/research/stock_screener.py
services/decision/src/research/strategy_architect.py
services/decision/src/research/strategy_evaluator.py
services/decision/src/research/symbol_profiler.py
services/decision/src/research/three_tier_optimizer.py
services/decision/src/research/trade_optimizer.py
services/decision/src/research/yaml_signal_executor.py
services/decision/src/stats/optimizer.py
```

### A3 白名单（待项目架构师预审后确定）
```
（根据预审结果确定具体文件清单）
```

---

## 5. 依赖关系

- A1 → A2 / A2-EX → A3（顺序执行）
- A1 必须优先完成（P0 安全漏洞）
- A2 和 A2-EX 可在 A1 完成后并行执行
- A3 可根据时间和资源情况选择性执行

---

## 6. 风险识别

### 高风险
- P0-1 代码注入：如果修复不当，可能影响 LLM 生成代码的正常执行
- P0-2 Prompt 注入：如果过滤过严，可能误杀正常输入

### 中风险
- P1-1 内存泄漏：修复可能影响信号分发性能
- P1-2 竞态条件：修复可能影响缓存命中率

### 低风险
- P2 代码质量：不影响功能，只影响可维护性

---

## 7. 验收标准

### A1 验收
- [ ] 所有 P0 漏洞修复完成
- [ ] 安全测试用例全部通过
- [ ] 现有功能测试全部通过
- [ ] 代码审查通过（项目架构师终审）

### A2 验收
- [ ] 所有 P1 问题修复完成
- [ ] 性能测试无回归
- [ ] 现有功能测试全部通过
- [ ] 代码审查通过（项目架构师终审）

### A3 验收
- [ ] 代码质量指标达标（测试覆盖率 > 80%、函数长度 < 100 行）
- [ ] 静态检查通过（mypy、pylint）
- [ ] 代码审查通过（项目架构师终审）

---

## 8. 执行计划

1. **A0 建档**（当前）：✅ 完成任务文档
2. **预审**：✅ 项目架构师审查通过（REVIEW-TASK-U0-20260418-002-PRE）
3. **P1-3 扫描**：✅ 发现 92 处 `except Exception`，涉及 39 个文件，建立 A2-EX 批次
4. **Token 签发**：⏳ 等待 Jay.S 签发 A1/A2/A2-EX 三枚 Token
5. **A1 实施**：修复 P0 严重漏洞（6 个文件）
6. **A1 终审**：项目架构师终审 A1 代码
7. **A2 实施**：修复 P1 中等问题（6 个文件）
8. **A2-EX 实施**：修复 P1-3 异常处理（39 个文件）
9. **A2/A2-EX 终审**：项目架构师终审 A2/A2-EX 代码
10. **A3 实施**（可选）：改进 P2 代码质量
11. **A3 终审**（可选）：项目架构师终审 A3 代码
12. **收口**：更新任务状态，lockback Token，同步到 Mini/Studio

---

## 9. 参考资料

- 代码审查报告：由 Agent a038dfd46934313a2 生成（2026-04-18）
- 审查范围：`services/decision/src/` 下所有 Python 代码（121 个文件）
- 审查方法：静态分析 + 模式匹配 + 最佳实践检查

---

## 10. 状态跟踪

- **A0 建档**：✅ 完成（2026-04-18）
- **预审**：✅ 完成（2026-04-18，REVIEW-TASK-U0-20260418-002-PRE）
- **P1-3 扫描**：✅ 完成（92 处，39 个文件，建立 A2-EX 批次）
- **Token 签发**：⏳ 等待 Jay.S 签发 A1/A2/A2-EX
- **A1 实施**：⏳ 待开始
- **A2 实施**：⏳ 待开始
- **A2-EX 实施**：⏳ 待开始
- **A3 实施**：⏳ 待开始（可选）
- **收口**：⏳ 待开始

---

【签名】Atlas  
【日期】2026-04-18  
【状态】预审通过，等待 Token 签发

## 11. Token 签发清单

### Token A1（P0 严重漏洞修复）
- **任务**：TASK-U0-20260418-002-A1
- **服务**：decision
- **文件数**：6 个（3 源码 + 3 测试）
- **有效期**：4320 分钟（3 天）
- **优先级**：P0（最高）

### Token A2（P1 中等问题修复）
- **任务**：TASK-U0-20260418-002-A2
- **服务**：decision
- **文件数**：6 个（3 源码 + 3 测试）
- **有效期**：4320 分钟（3 天）
- **优先级**：P1

### Token A2-EX（P1-3 异常处理专项）
- **任务**：TASK-U0-20260418-002-A2-EX
- **服务**：decision
- **文件数**：39 个
- **有效期**：4320 分钟（3 天）
- **优先级**：P1

---

【签名】Atlas  
【日期】2026-04-18  
【状态】等待 Jay.S 签发 Token
