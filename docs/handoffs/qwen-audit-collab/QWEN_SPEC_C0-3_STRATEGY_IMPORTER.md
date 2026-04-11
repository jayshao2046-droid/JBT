# Qwen Spec C0-3 Strategy Importer

## §1 任务摘要

目标：在 `services/decision/src/publish/` 新增 `strategy_importer.py` + `yaml_importer.py`，实现统一策略导入功能。

## §2 锚点声明

已存在：
- services/decision/src/publish/executor.py（策略执行器，新导入器需与其协作）
- services/decision/src/publish/gate.py（发布门禁，新导入器需与其协作）
- services/decision/src/publish/sim_adapter.py（模拟交易适配器，新导入器需与其协作）
- services/decision/src/model/router.py（模型路由，可参考其决策服务本地模型定义）

新建（本任务产出）：
- services/decision/src/publish/strategy_importer.py
- services/decision/src/publish/yaml_importer.py
- services/decision/src/api/routes/strategy_import.py（新路由文件，POST /api/v1/strategy/import）
- tests/decision/publish/test_strategy_importer.py

修改（本任务需追加注册）：
- services/decision/src/api/app.py（在 create_app() 中追加 app.include_router(strategy_import_router)）

planned-placeholder（不在本任务范围，不得引用）：
- （无，此任务不依赖任何 placeholder）

## §3 接口规范

### 路由路径
```
POST /api/v1/strategy/import
```

### HTTP 方法
```
POST
```

### 请求体 JSON Schema
```json
{
  "name": "string",
  "symbol": "string",
  "exchange": "string",
  "direction": "string",
  "entry_rules": {},
  "exit_rules": {},
  "risk_params": {},
  "source_type": "string",
  "content": "string"
}
```

### Query 参数
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| validate_only | boolean | 否 | 仅验证不保存，默认为 false |

### 响应 JSON Schema
```json
{
  "strategy_id": "string",
  "status": "string",
  "message": "string",
  "validation_errors": [],
  "strategy_data": {}
}
```

## §4 数据读取设计

### StrategyModel 定义
使用 decision 服务本地 `model/` 目录定义的策略模型，参考 `services/decision/src/model/router.py` 中的策略处理逻辑。

### 导入逻辑伪代码
```python
def import_strategy(
    strategy_data: dict,
    validate_only: bool = False
) -> dict[str, Any]:
    # 1. 验证策略数据格式
    validation_result = _validate_strategy_schema(strategy_data)
    if not validation_result.is_valid:
        return {
            "strategy_id": None,
            "status": "validation_failed",
            "message": "Invalid strategy schema",
            "validation_errors": validation_result.errors,
            "strategy_data": {}
        }
    
    # 2. 生成策略ID
    strategy_id = _generate_strategy_id(strategy_data)
    
    # 3. 如果仅验证，则返回验证结果
    if validate_only:
        return {
            "strategy_id": strategy_id,
            "status": "validated",
            "message": "Strategy validated successfully",
            "validation_errors": [],
            "strategy_data": strategy_data
        }
    
    # 4. 保存策略到仓库
    repo = get_repository()
    existing = repo.get(strategy_id)
    if existing:
        return {
            "strategy_id": strategy_id,
            "status": "duplicate",
            "message": f"Strategy {strategy_id} already exists",
            "validation_errors": [],
            "strategy_data": {}
        }
    
    # 5. 创建策略包并保存
    strategy_pkg = StrategyPackage(
        strategy_id=strategy_id,
        name=strategy_data.get("name"),
        symbol=strategy_data.get("symbol"),
        exchange=strategy_data.get("exchange"),
        direction=strategy_data.get("direction"),
        entry_rules=strategy_data.get("entry_rules"),
        exit_rules=strategy_data.get("exit_rules"),
        risk_params=strategy_data.get("risk_params"),
        source_type=strategy_data.get("source_type", "manual"),
        content=strategy_data.get("content"),
        created_at=datetime.now(_TZ_CST).isoformat(),
        updated_at=datetime.now(_TZ_CST).isoformat(),
        lifecycle_status=LifecycleStatus.draft
    )
    
    repo.save(strategy_pkg)
    
    return {
        "strategy_id": strategy_id,
        "status": "imported",
        "message": f"Strategy {strategy_id} imported successfully",
        "validation_errors": [],
        "strategy_data": strategy_pkg.to_dict()
    }
```

## §5 错误处理清单

| 错误场景 | HTTP 状态码 | 响应体格式 |
|----------|-------------|------------|
| 请求体格式错误 | 422 | {"detail": "JSON schema validation failed"} |
| 必需字段缺失 | 422 | {"detail": "Missing required field: [字段名]"} |
| 策略名称格式无效 | 422 | {"detail": "Invalid strategy name format"} |
| 策略已存在 | 409 | {"detail": "Strategy [ID] already exists"} |
| 内部处理错误 | 500 | {"detail": "Failed to import strategy: [错误详情]"} |

## §6 单元测试用例设计

| 用例ID | 前置条件 | 输入 | 预期输出 | 测试类型 |
|--------|----------|------|----------|----------|
| TC001 | 有效策略数据 | name="Test Strategy", symbol="000001", exchange="SZSE" | 成功导入策略 | happy |
| TC002 | 有效策略数据 | name="期货策略", symbol="cu2303", exchange="SHFE", direction="long" | 成功导入策略 | happy |
| TC003 | 有效策略数据 | name="股票策略", symbol="600000", exchange="SSE", direction="short" | 成功导入策略 | happy |
| TC004 | 有效策略数据 | name="多规则策略", entry_rules={"ma": 5}, exit_rules={"ma": 20}, risk_params={"max_loss": 0.05} | 成功导入策略 | happy |
| TC005 | 仅验证模式 | validate_only=true, name="Test Strategy", symbol="000001" | 返回验证成功结果 | happy |
| TC006 | 策略名称格式无效 | name="", symbol="000001", exchange="SZSE" | HTTP 422 错误 | error |
| TC007 | 必需字段缺失 | exchange="SZSE", symbol="000001" (缺少name) | HTTP 422 错误 | error |

## §7 依赖关系确认

- 本任务无前置依赖（Lane-A 首发）
- 解锁：CF2（依赖本任务）、C0-2（与C0-1共同完成后解锁）