# TASK-0119: 安全漏洞全面修复派工单

**任务编号**: TASK-0119  
**创建时间**: 2026-04-15  
**派工对象**: Claude-Code  
**任务类型**: U0 终极维护模式 - 安全漏洞修复  
**优先级**: P0（紧急）  
**依据报告**: `docs/reports/20260415-风控常规体检报告.md`

---

## 📋 任务概述

根据 2026-04-15 风控常规体检报告，发现 4 个高危漏洞（P0）、7 个中危漏洞（P1）、6 个低危问题（P2）。本任务将按照 U0 终极维护模式执行全部修复。

---

## 🎯 修复范围

### 批次 A：data 服务紧急安全修复（P0）
**优先级**: 最高  
**涉及服务**: `services/data/`

#### 修复项目：
1. **P0-1**: API 认证绕过漏洞
2. **P0-2**: 命令注入风险（ops 端点）
3. **P0-4**: 敏感信息泄露（错误消息）
4. **P1-4**: 飞书通知 Token 泄露
5. **P1-7**: 数据采集器 Token 文件读取不安全

#### 需要修改的文件：
- `services/data/src/main.py` - 认证、命令注入、错误处理
- `services/data/src/notify/card_templates.py` - Token 泄露
- `services/data/src/collectors/tushare_full_collector.py` - Token 读取
- `services/data/tests/test_main.py` - 新增测试
- `services/data/tests/test_security.py` - 新增安全测试

---

### 批次 B：decision 服务安全加固（P0 + P1）
**优先级**: 高  
**涉及服务**: `services/decision/`

#### 修复项目：
1. **P0-3**: LLM Prompt 注入漏洞
2. **P1-1**: 信号分发器内存泄漏
3. **P1-2**: 邮件通知 HTML 注入
4. **P1-3**: 状态存储文件权限问题
5. **P1-6**: JSON 解析异常处理不完整

#### 需要修改的文件：
- `services/decision/src/llm/gate_reviewer.py` - Prompt 注入防护
- `services/decision/src/core/signal_dispatcher.py` - 内存泄漏
- `services/decision/src/notifier/email.py` - HTML 注入
- `services/decision/src/persistence/state_store.py` - 文件权限
- `services/decision/tests/test_llm_security.py` - 新增安全测试
- `services/decision/tests/test_signal_dispatcher.py` - 内存泄漏测试

---

### 批次 C：data 服务爬虫安全加固（P1 + P2）
**优先级**: 中  
**涉及服务**: `services/data/`

#### 修复项目：
1. **P1-5**: 爬虫 XPath 注入风险
2. **P2-1**: 过于宽泛的异常捕获
3. **P2-2**: 缺少输入验证

#### 需要修改的文件：
- `services/data/src/researcher/crawler/parsers/futures.py` - XPath 安全
- `services/data/src/researcher/scheduler.py` - 异常处理
- `services/decision/src/research/factor_loader.py` - 输入验证

---

### 批次 D：通用安全增强（P2）
**优先级**: 低  
**涉及服务**: 多个服务

#### 修复项目：
1. **P2-3**: 硬编码的超时值
2. **P2-4**: 缺少速率限制
3. **P2-5**: 并发安全问题
4. **P2-6**: 缺少日志审计

#### 需要修改的文件：
- `services/decision/src/llm/gate_reviewer.py` - 超时配置
- `services/decision/src/api/app.py` - 速率限制
- `services/decision/src/research/sandbox_engine.py` - 并发锁
- `services/data/src/main.py` - 审计日志

---

## 📁 完整文件白名单

### 批次 A（data 服务紧急修复）
```
services/data/src/main.py
services/data/src/notify/card_templates.py
services/data/src/collectors/tushare_full_collector.py
services/data/tests/test_main.py
services/data/tests/test_security.py
```

### 批次 B（decision 服务安全加固）
```
services/decision/src/llm/gate_reviewer.py
services/decision/src/core/signal_dispatcher.py
services/decision/src/notifier/email.py
services/decision/src/persistence/state_store.py
services/decision/tests/test_llm_security.py
services/decision/tests/test_signal_dispatcher.py
```

### 批次 C（爬虫安全加固）
```
services/data/src/researcher/crawler/parsers/futures.py
services/data/src/researcher/scheduler.py
services/decision/src/research/factor_loader.py
```

### 批次 D（通用安全增强）
```
services/decision/src/llm/gate_reviewer.py
services/decision/src/api/app.py
services/decision/src/research/sandbox_engine.py
services/data/src/main.py
```

---

## ✅ 验收标准

### 功能验收
1. 所有 P0 漏洞修复后，通过安全测试
2. API 认证在未配置 Key 时正确拒绝请求
3. ops 端点严格验证 plist_id 格式和路径
4. LLM prompt 注入防护生效
5. 信号分发器内存不再泄漏

### 测试覆盖
1. 新增安全测试用例覆盖所有 P0 漏洞
2. 内存泄漏测试验证 FIFO 淘汰逻辑
3. Prompt 注入测试验证过滤机制

### 文档更新
1. 在风控体检报告末尾追加修复记录
2. 记录所有修改的文件和代码行数
3. 记录修复前后的对比

---

## 🔒 治理流程

1. **Atlas 确认**: 批准本派工单和文件白名单
2. **项目架构师预审**: 审查修复方案，冻结白名单
3. **Jay.S 签发 Token**: 为白名单文件签发 Token
4. **Claude-Code 实施**: 按批次执行修复
5. **批次收口**: 每批次完成后调用 `append_atlas_log`
6. **终审和锁回**: Atlas 复审 → 架构师终审 → lockback → commit

---

## 📊 预估工作量

- **批次 A**: 2 小时（紧急）
- **批次 B**: 3 小时
- **批次 C**: 1.5 小时
- **批次 D**: 2 小时
- **测试编写**: 2 小时
- **文档更新**: 0.5 小时

**总计**: 约 11 小时

---

## 🚨 风险提示

1. **data 服务修复需要重启**: 修复后需要重启 Mini 上的 data 服务
2. **decision 服务修复需要重启**: 修复后需要重启 Studio 上的 decision 服务
3. **API Key 配置检查**: 修复后必须确保所有环境都配置了 API Key
4. **向后兼容性**: 所有修复保持 API 向后兼容

---

## 📝 备注

- 本任务遵循 U0 终极维护模式
- 所有修复必须通过测试验证
- 修复完成后更新风控体检报告
- 两地同步（Mini/Studio）

---

**派工签名**: Claude-Code  
**等待审批**: Atlas → 项目架构师 → Jay.S Token 签发
