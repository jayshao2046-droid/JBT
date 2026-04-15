"""
测试 /api/v1/bars 端点

验证端点支持：
1. 必填参数：symbol, start
2. 可选参数：end, limit, timeframe_minutes
3. end 默认为当前时间
4. limit 限制返回条数
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


def test_bars_with_start_only(client: TestClient):
    """测试只提供 start 参数（end 默认为当前时间）"""
    start = (datetime.now() - timedelta(hours=1)).isoformat()

    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "KQ.m@SHFE.rb",
            "start": start,
        }
    )

    # 如果数据不存在，返回 404 是正常的
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "bars" in data
        assert "count" in data
        assert isinstance(data["bars"], list)


def test_bars_with_start_end(client: TestClient):
    """测试提供 start 和 end 参数"""
    end = datetime.now()
    start = end - timedelta(hours=1)

    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "KQ.m@SHFE.rb",
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "bars" in data
        assert "count" in data


def test_bars_with_limit(client: TestClient):
    """测试 limit 参数限制返回条数"""
    start = (datetime.now() - timedelta(days=7)).isoformat()

    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "KQ.m@SHFE.rb",
            "start": start,
            "limit": 10,
        }
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "bars" in data
        assert "count" in data
        # 如果有数据，验证返回条数不超过 limit
        if data["count"] > 0:
            assert data["count"] <= 10
            assert len(data["bars"]) <= 10


def test_bars_invalid_symbol(client: TestClient):
    """测试无效的 symbol"""
    start = (datetime.now() - timedelta(hours=1)).isoformat()

    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "INVALID_SYMBOL",
            "start": start,
        }
    )

    # 无效 symbol 应该返回 422 或 404
    assert response.status_code in [422, 404]


def test_bars_missing_required_params(client: TestClient):
    """测试缺少必填参数"""
    # 缺少 symbol
    response = client.get(
        "/api/v1/bars",
        params={
            "start": datetime.now().isoformat(),
        }
    )
    assert response.status_code == 422

    # 缺少 start
    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "KQ.m@SHFE.rb",
        }
    )
    assert response.status_code == 422


def test_bars_end_before_start(client: TestClient):
    """测试 end 早于 start 的情况"""
    end = datetime.now()
    start = end + timedelta(hours=1)  # start 晚于 end

    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "KQ.m@SHFE.rb",
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
    )

    assert response.status_code == 422
    assert "end must be greater than or equal to start" in response.json()["detail"]


def test_bars_response_structure(client: TestClient):
    """测试响应结构"""
    start = (datetime.now() - timedelta(hours=1)).isoformat()

    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "KQ.m@SHFE.rb",
            "start": start,
        }
    )

    if response.status_code == 200:
        data = response.json()

        # 验证必需字段
        assert "requested_symbol" in data
        assert "resolved_symbol" in data
        assert "source_kind" in data
        assert "timeframe_minutes" in data
        assert "count" in data
        assert "bars" in data

        # 验证字段类型
        assert isinstance(data["requested_symbol"], str)
        assert isinstance(data["resolved_symbol"], str)
        assert isinstance(data["source_kind"], str)
        assert isinstance(data["timeframe_minutes"], int)
        assert isinstance(data["count"], int)
        assert isinstance(data["bars"], list)

        # 如果有数据，验证 bar 结构
        if data["bars"]:
            bar = data["bars"][0]
            assert "datetime" in bar or "timestamp" in bar
            assert "open" in bar
            assert "high" in bar
            assert "low" in bar
            assert "close" in bar
            assert "volume" in bar
