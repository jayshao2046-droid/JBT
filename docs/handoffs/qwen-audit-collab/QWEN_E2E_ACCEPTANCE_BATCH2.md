# Qwen E2E Acceptance Batch2

## §1 C0-1 验收场景（最少 5 条）

| 场景ID | 描述 | 操作步骤 | 预期结果 | 验收方式 |
|--------|------|----------|----------|----------|
| SC001 | 股票分钟K线查询 | 1. 调用 `/api/v1/stocks/bars` 接口<br>2. 传入有效的股票代码和时间范围 | 返回指定股票的分钟K线数据 | curl |
| SC002 | 股票日K线查询 | 1. 调用 `/api/v1/stocks/bars` 接口<br>2. 传入 `timeframe_minutes=1440` | 返回指定股票的日K线数据 | curl |
| SC003 | 无效股票代码查询 | 1. 调用 `/api/v1/stocks/bars` 接口<br>2. 传入不存在的股票代码 | 返回 404 错误 | curl |
| SC004 | 时间范围错误查询 | 1. 调用 `/api/v1/stocks/bars` 接口<br>2. 传入 end 时间早于 start 时间 | 返回 422 错误 | curl |
| SC005 | 股票数据格式验证 | 1. 查询任意股票K线数据<br>2. 检查返回数据格式 | 返回数据符合预定义的 JSON Schema | pytest |

## §2 C0-3 验收场景（最少 4 条）

| 场景ID | 描述 | 操作步骤 | 预期结果 | 验收方式 |
|--------|------|----------|----------|----------|
| SC006 | 有效策略导入 | 1. 调用 `/api/v1/strategy/import` 接口<br>2. 传入符合 schema 的策略数据 | 成功导入策略，返回策略ID | curl |
| SC007 | 策略验证模式 | 1. 调用 `/api/v1/strategy/import` 接口<br>2. 设置 `validate_only=true`<br>3. 传入策略数据 | 返回验证结果，不实际保存策略 | curl |
| SC008 | 无效策略数据导入 | 1. 调用 `/api/v1/strategy/import` 接口<br>2. 传入缺少必需字段的策略数据 | 返回 422 错误，包含验证错误信息 | curl |
| SC009 | 重复策略导入 | 1. 成功导入一个策略<br>2. 再次导入相同ID的策略 | 返回 409 错误，提示策略已存在 | curl |

## §3 CG1 验收场景（最少 4 条）

| 场景ID | 描述 | 操作步骤 | 预期结果 | 验收方式 |
|--------|------|----------|----------|----------|
| SC010 | 策略入队 | 1. 调用 `/api/v1/strategy-queue/enqueue` 接口<br>2. 传入策略数据 | 成功入队，返回队列ID | curl |
| SC011 | 队列状态查询 | 1. 向队列添加几个项目<br>2. 调用 `/api/v1/strategy-queue/status` 接口 | 返回队列中所有项目的状态信息 | curl |
| SC012 | 队列清空 | 1. 向队列添加几个项目<br>2. 调用 `/api/v1/strategy-queue/clear` 接口 | 队列被清空，返回成功信息 | curl |
| SC013 | 队列优先级验证 | 1. 添加多个不同优先级的策略到队列<br>2. 查询队列状态 | 高优先级策略排在前面 | curl |

## §4 回归测试覆盖确认

### data 服务需要在 C0-1 实施后做回归验证的路由
- `/api/v1/bars` - 期货K线查询（确保新增股票路由不影响现有功能）
- `/api/v1/symbols` - 符号列表查询（确保数据结构一致性）
- `/api/v1/health` - 健康检查（确保服务正常运行）
- `/api/v1/version` - 版本信息（确保服务正常运行）

### backtest 服务需要在 CG1 实施后做回归验证的路由
- `/api/strategy/import` （现有策略导入，前缀 /api）
- `/api/strategy/{name}` （现有策略详情）
- `/api/strategies` （现有策略列表）
- `/api/v1/health` （健康检查）

> Atlas 补漏（2026-04-11）：backtest 服务路由由 `api/app.py` create_app() 管理，小写路由前缀为 `/api`（非 `/api/v1`）。