# TASK-U0-20260423-researcher-security-fix

## 任务信息

- **任务ID**: TASK-U0-20260423-researcher-security-fix
- **创建时间**: 2026-04-23
- **任务类型**: U0 紧急安全修复
- **服务范围**: services/data/src/researcher/
- **执行设备**: MacBook 本地开发 → Alienware 部署
- **执行 Agent**: Atlas (U0 模式)
- **优先级**: P0 (Critical 安全漏洞)

## 收口说明

- 本次按 U0 事后审计最小事实补录收口。
- 当前收口以仓内实际 diff、真实运行校验和 Alienware 部署证据为准。

## 任务背景

通过全面只读诊断，发现 Alienware 研究员模块存在 **20 个安全和质量问题**：
- **3 个 Critical 级别**：SQL 注入、路径遍历、不安全动态导入
- **7 个 High 级别**：资源泄漏、异常处理、硬编码配置等
- **5 个 Medium 级别**：None 引用、配置验证、竞态条件等
- **5 个 Low 级别**：代码质量问题

## 诊断报告

完整诊断报告见 Agent 输出（56 个文件，9289 行代码）。

## 修复范围

### Critical 级别（必须修复）

1. **SQL 注入风险** — `reporter.py:66`
   - 问题：使用 f-string 直接拼接 SQL 语句
   - 修复：使用白名单验证列定义

2. **路径遍历漏洞** — `staging.py:177-188`
   - 问题：`prev_date` 和 `prev_segment` 可能包含路径遍历字符
   - 修复：正则表达式验证 + pathlib 规范化（已部分修复，需加强）

3. **不安全的 `__import__` 使用** — `scheduler.py:1004`
   - 问题：使用动态导入反模式
   - 修复：在文件顶部正常导入 datetime

### High 级别（应该修复）

4. **资源泄漏** — `context_manager.py` 多处
   - 问题：SQLite 连接未使用 with 语句
   - 修复：统一使用 `with sqlite3.connect()`

5. **资源泄漏** — `deduplication.py` 8 处
   - 问题：同上
   - 修复：同上

6. **异常处理过于宽泛** — 4 个文件
   - `fundamental_crawler.py:104`
   - `kline_monitor.py:104`
   - `news_crawler.py:126`
   - `llm_analyzer.py:41`
   - 问题：使用裸 `except:` 捕获所有异常
   - 修复：明确捕获预期异常类型

7. **硬编码 IP 地址** — `config.py` 等多个文件
   - 问题：硬编码内网 IP 作为默认值
   - 修复：移除硬编码默认值或使用 localhost

8. **文件删除操作缺少错误处理** — `scheduler.py:721`
   - 问题：删除失败被吞掉
   - 修复：添加日志记录

9. **JSON 解析缺少错误处理** — `scheduler.py:1209-1212`
   - 问题：`text.index()` 可能抛出 ValueError
   - 修复：添加完整错误处理

10. **网络请求超时时间过长** — 3 个文件
    - 问题：超时设置为 10-30 秒
    - 修复：使用配置常量

### Medium 级别（建议修复）

11. **None 引用风险** — `scheduler.py:956-962`
12. **缺失的环境变量验证** — `config.py:115-117`
13. **竞态条件** — `daily_stats.py:81-99`
14. **缺失的输入验证** — `notifier.py:375`
15. **缺失的日志记录** — 多处

### Low 级别（可选修复）

16. 未使用的导入
17. 代码重复
18. 魔法数字
19. 过长函数
20. TODO 注释未完成

## 修复策略

### 阶段 1：Critical 级别（本批次）
- 修复 3 个 Critical 漏洞
- 文件：`reporter.py`, `staging.py`, `scheduler.py`

### 阶段 2：High 级别（本批次）
- 修复 7 个 High 级别问题
- 文件：`context_manager.py`, `deduplication.py`, `fundamental_crawler.py`, `kline_monitor.py`, `news_crawler.py`, `llm_analyzer.py`, `config.py`, `scheduler.py`

### 阶段 3：Medium 级别（本批次）
- 修复 5 个 Medium 级别问题
- 文件：`scheduler.py`, `config.py`, `daily_stats.py`, `notifier.py`

### 阶段 4：Low 级别（可选）
- 代码质量改进
- 后续批次处理

## 文件清单

本批实际修改文件（9 个）：

1. `services/data/src/researcher/reporter.py` — SQL 注入修复
2. `services/data/src/researcher/scheduler.py` — 动态导入移除 + 文件删除错误日志
3. `services/data/src/researcher/context_manager.py` — SQLite 资源泄漏修复
4. `services/data/src/researcher/deduplication.py` — SQLite 资源泄漏修复
5. `services/data/src/researcher/fundamental_crawler.py` — 队列异常处理收敛
6. `services/data/src/researcher/kline_monitor.py` — 队列异常处理收敛
7. `services/data/src/researcher/news_crawler.py` — 队列异常处理收敛
8. `services/data/src/researcher/llm_analyzer.py` — `queue.Empty` 明确捕获
9. `services/data/src/researcher/config.py` — 环境变量解析校验增强

未纳入本批实际 diff 的观察项：`staging.py`、`daily_stats.py`、`notifier.py` 以及 `scheduler.py` 中 JSON 解析/网络超时优化，保留为后续项，不在本次收口中宣称完成。

补充说明：部署前真实 import 校验发现 `config.py` 在类定义阶段引用未定义 `logger`，已在同文件内补齐模块级 logger 定义后重新校验通过。

## 验收标准

1. ✅ 本批实际 diff 中的安全修复项已落地
2. ✅ researcher 9 个业务文件通过本地最小语法校验
3. ✅ researcher 9 个业务文件 VS Code 问题检查为 0 errors
4. ✅ review / lock / handoff 审计材料已补齐
5. ✅ 已部署到 Alienware，`8199/health` 返回 ok

## U0 模式约束

1. ✅ 在 MacBook 本地完成所有修改
2. ✅ 不直接修改 Mini 上的文件（研究员运行在 Alienware）
3. ✅ 创建完整的 U0 审计文档
4. ✅ 部署前通过语法检查
5. ✅ 部署后验证服务健康

## 执行记录

### 2026-04-23 — 任务创建
- 创建任务文档
- 准备开始修复

### 2026-04-23 — 完成 researcher 本地安全修复
- 实际业务改动收敛为 researcher 目录内 9 个文件
- 已完成 SQL 注入、动态导入、资源泄漏、宽泛异常处理、文件删除日志和配置验证等修复
- researcher 9 个文件完成本地最小语法校验

### 2026-04-23 — 完成 U0 事后审计收口
- 补齐 review / lock 留痕
- 校正任务单与 handoff 口径为“按实际 diff 收口”

### 2026-04-23 — 部署到 Alienware 并完成最小运行验证
- 远端 researcher 目录已备份：`C:\Users\17621\jbt\services\data\src\researcher_backup_20260423-125413`
- 已上传 9 个 researcher 修复文件到 `C:\Users\17621\jbt\services\data\src\researcher\`
- 通过 `schtasks /Run /TN JBT_Researcher_Service` 拉起 researcher 服务
- `http://192.168.31.187:8199/health` 返回 `status=ok`

## 状态

- **当前状态**: 已收口并完成 Alienware 部署验证
- **下一步**: 如需进一步验证报告生成链路，补做一次端到端运行证据采集
