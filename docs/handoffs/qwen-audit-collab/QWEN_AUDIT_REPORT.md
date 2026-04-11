# Qwen Audit Report

【签名】Qwen
【时间】2026-04-11
【设备】MacBook

## 1. 审查范围与方法

### 审查范围
- JBT当前工作区根目录下所有文件（排除`.venv/`第三方库源码）
- 主要服务目录：services/data/, services/backtest/, services/decision/, services/sim-trading/
- 治理文件：governance/, .roo/, docs/
- 共享契约：shared/

### 审查方法
1. **静态代码扫描**：使用正则表达式搜索潜在安全问题模式
2. **手动代码审查**：对识别出的风险点进行逐行上下文分析
3. **数据流分析**：跟踪用户输入到敏感操作的路径
4. **依赖清单检查**：检查requirements文件，不深入第三方库实现

## 2. 执行摘要

本次审查对JBT项目进行了只读安全审计，重点检查了代码安全模式和实现风险。审查基于代码静态分析，未涉及运行时测试。

**证实发现**：
1. 未发现P0级别（立即阻断性）安全问题
2. 发现1个P1级别（高风险）问题：回测策略表达式求值使用`eval()`（F-001）
3. 发现2个P2级别（中风险）问题：subprocess调用安全模式、SQL拼接模式

**推断待验证**：
1. subprocess调用的输入可控性需要运行时验证
2. 依赖库版本可能存在已知漏洞，需要专项扫描

**总体评估**：项目代码安全基线基本合格，但在策略表达式执行和外部命令执行模式上存在可改进的安全实践。

## 3. 发现清单

### P0
**本轮未发现P0级别问题**

### P1

#### F-001 - 策略表达式求值使用eval()
- **严重度**：P1
- **标题**：回测引擎使用eval()执行用户/配置提供的表达式
- **证据文件**：`services/backtest/src/backtest/generic_strategy.py:1373-1384`
- **代码引用**：
  ```python
  def _safe_eval_expression(expression: str, environment: Mapping[str, Any]) -> Any:
      prepared = _prepare_expression(expression)
      try:
          tree = ast.parse(prepared, mode="eval")
          _SafeExpressionValidator(set(environment) | set(_ALLOWED_FUNCTIONS)).visit(tree)
          return eval(
              compile(tree, "<generic-strategy-expression>", "eval"),
              {"__builtins__": {}},
              {**_ALLOWED_FUNCTIONS, **dict(environment)},
          )
  ```
- **问题描述**：策略引擎使用`eval()`执行策略表达式。虽然有`_SafeExpressionValidator`进行AST检查和`__builtins__`限制，但`eval()`本身是高风险操作。如果验证器存在漏洞或环境变量被污染，可能导致任意代码执行。
- **影响范围**：回测服务策略执行引擎。影响所有使用generic_strategy模板的策略。
- **建议修复方向**：
  1. 考虑使用沙箱环境（如`RestrictedPython`、`PySandbox`）
  2. 实施表达式复杂度限制和深度限制
  3. 增加表达式执行监控和审计日志
  4. **推断，待验证**：需要审查`_SafeExpressionValidator`的实现完整性和`_ALLOWED_FUNCTIONS`白名单

### P2

#### F-002 - subprocess调用模式可能被复制用于动态输入
- **严重度**：P2
- **标题**：多个模块使用subprocess.run，代码模式可能在不安全上下文中被复制
- **证据文件**：
  - `services/data/src/collectors/overseas_minute_collector.py:414-417`（curl调用）
  - `services/data/src/scheduler/data_scheduler.py:1275-1279`（bash脚本执行）
  - `services/data/src/ops/backup.py:70`（rsync调用）
- **问题描述**：代码中存在多个subprocess.run调用实例。分析发现：
  1. `overseas_minute_collector.py`：curl命令URL包含API密钥，但密钥来自环境变量，URL构造无用户输入
  2. `data_scheduler.py`：执行固定bash脚本，使用`nosec`注释绕过安全检查
  3. `backup.py`：rsync参数可能包含动态路径
- **风险分析**：
  - 当前调用多数使用固定或配置驱动参数，未发现直接用户输入注入
  - `nosec`注释表明开发者意识到安全风险但选择绕过
  - 代码模式可能在不安全上下文中被复制（如接收用户输入的场景）
- **影响范围**：数据服务（collectors, scheduler, ops模块）
- **建议修复方向**：
  1. 移除`nosec`注释，实施实际安全控制或记录风险评估
  2. 创建安全的命令执行工具函数，统一处理参数验证和转义
  3. 对动态参数实施严格的输入验证
  4. **推断，待验证**：需要运行时验证各调用点的输入来源

#### F-003 - DuckDB查询使用字符串拼接模式
- **严重度**：P2
- **标题**：SQL查询构建使用f-string拼接，存在模式风险
- **证据文件**：`services/data/src/data/storage.py:149-153`
- **代码引用**：
  ```python
  sql = f"SELECT {selected} FROM read_parquet('{file_path.as_posix()}')"  # nosec B608 — file_path is a Path object, not user input
  if sql_where:
      sql += f" WHERE {sql_where}"
  if order_by:
      sql += f" ORDER BY {order_by}"
  ```
- **问题描述**：使用f-string拼接SQL查询，特别是WHERE和ORDER BY子句的动态拼接（lines 150-153），存在查询构造链风险。虽然当前上下文`file_path`是Path对象，但sql_where和order_by参数的来源需要验证，以确保不存在用户输入直接拼接到查询中的情况。
- **影响范围**：数据存储模块，查询构造链安全风险
- **建议修复方向**：
  1. 验证sql_where和order_by参数的来源和内容，确保经过适当清理和验证
  2. 考虑使用参数化查询或查询构建器来处理WHERE和ORDER BY子句
  3. 实施输入验证机制，防止恶意查询片段注入

### 从主清单移除的问题

以下问题从主发现清单移除，转入"不确定但值得复查的问题"：

1. **原F-002（API密钥日志泄露）**：重新审查发现日志仅输出配置状态（bool值），不包含实际密钥。风险较低。
2. **原F-004（HTTP端点输入验证）**：重新审查发现使用HMAC比较，设计基本合理。输入验证强化属于增强性改进。
3. **原F-006（第三方库内部实现）**：第三方库源码（.venv/）不应作为项目自身安全问题。转为依赖版本审查。
4. **原F-007（配置文件权限）**：文件权限检查属于部署运维范畴，非代码安全问题。

## 4. 可延后问题

1. **subprocess调用输入来源验证**：需要运行时分析验证各调用点输入是否可控
2. **表达式验证器安全审查**：需要专项审查`_SafeExpressionValidator`和`_ALLOWED_FUNCTIONS`
3. **SQL模式重构**：当前风险较低，可在代码重构时优化

## 5. 不确定但值得复查的问题

1. **依赖版本与已知漏洞复查**
   - **问题**：项目依赖的第三方库版本可能存在已知安全漏洞
   - **审查方法**：使用安全扫描工具（Safety、Trivy、Dependabot）检查requirements文件
   - **预期产出**：依赖漏洞报告和升级建议
   - **证据文件**：`requirements.txt`、`pyproject.toml`、各服务requirements文件

2. **部署与配置治理复查**
   - **问题**：生产环境配置、文件权限、密钥管理需要专项检查
   - **审查方法**：部署清单审计、配置模板检查、权限验证
   - **预期产出**：部署安全配置规范
   - **证据文件**：`.env.example`、`docker-compose.*.yml`、部署文档

3. **内存安全与凭证处理**
   - **问题**：敏感信息在内存中的处理安全（如SimNow网关凭证）
   - **审查方法**：代码审查、安全模式分析
   - **预期产出**：内存安全最佳实践指南
   - **证据文件**：`services/sim-trading/src/api/router.py`、`governance/jbt_lockctl.py`

## 6. 总体风险结论

基于当前代码静态分析，JBT项目安全状况**基本合格**，未发现必须立即阻断的严重漏洞。主要观察如下：

1. **证实风险**：回测策略表达式使用`eval()`是确实存在的P1风险，需要专项处理
2. **模式风险**：subprocess和SQL拼接模式存在潜在风险，需要防止在不安全上下文中复制
3. **推断风险**：依赖漏洞、配置安全等需要专项验证

**建议优先级**：
1. 专项处理F-001（表达式求值安全）
2. 建立安全代码模式规范，防止风险模式扩散
3. 开展依赖安全专项扫描

**风险评估**：在当前使用场景（内部或受控环境）下风险可控，但在公开或多租户环境中部署前需完成关键安全问题修复。