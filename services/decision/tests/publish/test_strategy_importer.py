"""
策略导入解析器测试 — TASK-0051 C0-3
覆盖：成功导入、仅验证模式、重复导入、缺失字段、YAML 解析、路由层。
"""
import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import create_app
from src.publish.strategy_importer import (
    StrategyPackage,
    StrategyRepository,
    LifecycleStatus,
    import_strategy,
    _validate_strategy_schema,
    _generate_strategy_id,
    reset_import_repository,
)
from src.publish.yaml_importer import parse_yaml_strategy, validate_yaml_schema


# ─── fixtures ────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean_repo():
    """每个测试前后重置全局仓库。"""
    reset_import_repository()
    yield
    reset_import_repository()


@pytest.fixture
def repo():
    return StrategyRepository()


@pytest.fixture
def app():
    return create_app()


_VALID_DATA = {
    "name": "双均线交叉",
    "symbol": "000001",
    "exchange": "SZSE",
    "direction": "long",
    "entry_rules": {"ma_fast": 5, "ma_slow": 20},
    "exit_rules": {"stop_loss": 0.03},
    "risk_params": {"max_position": 0.1},
    "source_type": "manual",
    "content": "",
}


# ─── 1. 成功导入 ────────────────────────────────────────────────────


def test_import_success(repo: StrategyRepository) -> None:
    result = import_strategy(_VALID_DATA, repo=repo)
    assert result["status"] == "imported"
    assert result["strategy_id"] is not None
    assert result["strategy_data"]["name"] == "双均线交叉"
    assert result["strategy_data"]["lifecycle_status"] == "draft"
    # 确认存储
    assert repo.get(result["strategy_id"]) is not None


# ─── 2. 仅验证模式 ──────────────────────────────────────────────────


def test_import_validate_only(repo: StrategyRepository) -> None:
    result = import_strategy(_VALID_DATA, validate_only=True, repo=repo)
    assert result["status"] == "validated"
    assert result["strategy_id"] is not None
    assert result["strategy_data"] is None
    # 不应保存
    assert repo.get(result["strategy_id"]) is None


# ─── 3. 重复导入 ─────────────────────────────────────────────────────


def test_import_duplicate(repo: StrategyRepository) -> None:
    import_strategy(_VALID_DATA, repo=repo)
    result = import_strategy(_VALID_DATA, repo=repo)
    assert result["status"] == "conflict"
    assert result["message"] == "策略已存在"


# ─── 4. 缺失必填字段 ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "missing_field",
    ["name", "symbol", "exchange"],
)
def test_import_missing_field(missing_field: str, repo: StrategyRepository) -> None:
    data = {**_VALID_DATA}
    del data[missing_field]
    result = import_strategy(data, repo=repo)
    assert result["status"] == "validation_failed"
    assert any(missing_field in err for err in result["validation_errors"])


# ─── 5. 空白字段视为缺失 ────────────────────────────────────────────


def test_import_blank_field(repo: StrategyRepository) -> None:
    data = {**_VALID_DATA, "name": "   "}
    result = import_strategy(data, repo=repo)
    assert result["status"] == "validation_failed"


# ─── 6. YAML 解析成功 ───────────────────────────────────────────────


def test_yaml_parse_success() -> None:
    yaml_content = """
name: MACD策略
symbol: "600000"
exchange: SSE
direction: long
entry_rules:
  fast_period: 12
  slow_period: 26
"""
    data = parse_yaml_strategy(yaml_content)
    assert data["name"] == "MACD策略"
    assert data["symbol"] == "600000"
    errors = validate_yaml_schema(data)
    assert errors == []


# ─── 7. YAML 解析失败 ───────────────────────────────────────────────


def test_yaml_parse_invalid() -> None:
    with pytest.raises(ValueError):
        parse_yaml_strategy(":::invalid yaml{{{")


def test_yaml_parse_empty() -> None:
    with pytest.raises(ValueError, match="YAML 内容不能为空"):
        parse_yaml_strategy("")


# ─── 8. YAML schema 校验缺失字段 ────────────────────────────────────


def test_yaml_validate_schema_missing() -> None:
    data = {"name": "test"}  # 缺 symbol, exchange
    errors = validate_yaml_schema(data)
    assert len(errors) == 2


# ─── 9. 策略 ID 确定性 ──────────────────────────────────────────────


def test_strategy_id_deterministic() -> None:
    id1 = _generate_strategy_id("test", "000001", "SZSE")
    id2 = _generate_strategy_id("test", "000001", "SZSE")
    assert id1 == id2
    assert id1.startswith("strat-")


# ─── 10. 路由层 — 成功导入 ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_route_import_success(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/strategy-import/import", json=_VALID_DATA)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "imported"
    assert body["strategy_id"] is not None


# ─── 11. 路由层 — 仅验证 ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_route_validate_only(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/strategy-import/import",
            json=_VALID_DATA,
            params={"validate_only": "true"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "validated"


# ─── 12. 路由层 — 重复导入 409 ──────────────────────────────────────


@pytest.mark.asyncio
async def test_route_duplicate_409(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/strategy-import/import", json=_VALID_DATA)
        resp = await client.post("/strategy-import/import", json=_VALID_DATA)
    assert resp.status_code == 409
