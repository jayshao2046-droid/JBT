# TASK-0022-B: 只读日志查看 API 测试

import logging

from src.main import memory_log_handler


def _clear_log_handler():
    memory_log_handler.records.clear()


def test_logs_returns_correct_structure(client):
    """GET /api/v1/logs 返回 {logs: [...], total: N} 结构"""
    resp = client.get("/api/v1/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert "logs" in data
    assert "total" in data
    assert isinstance(data["logs"], list)
    assert isinstance(data["total"], int)


def test_logs_limit_parameter(client):
    """limit 参数限制返回条数"""
    _clear_log_handler()
    logger = logging.getLogger("test.limit")
    for i in range(20):
        logger.info("log entry %d", i)

    resp = client.get("/api/v1/logs?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] <= 5
    assert len(data["logs"]) <= 5


def test_logs_level_filter(client):
    """level 参数过滤日志级别"""
    _clear_log_handler()
    logger = logging.getLogger("test.level")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")

    resp = client.get("/api/v1/logs?level=ERROR")
    assert resp.status_code == 200
    data = resp.json()
    for entry in data["logs"]:
        assert entry["level"] == "ERROR"


def test_logs_source_filter(client):
    """source 参数按来源过滤"""
    _clear_log_handler()
    logging.getLogger("mysource.a").info("from a")
    logging.getLogger("othersource.b").info("from b")

    resp = client.get("/api/v1/logs?source=mysource")
    assert resp.status_code == 200
    data = resp.json()
    for entry in data["logs"]:
        assert "mysource" in entry["source"]


def test_logs_empty_returns_empty_list(client):
    """日志为空时返回空列表"""
    _clear_log_handler()
    resp = client.get("/api/v1/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["logs"] == []
    assert data["total"] == 0


def test_logs_tail_returns_same_structure(client):
    """GET /api/v1/logs/tail 结构与 /logs 一致"""
    resp = client.get("/api/v1/logs/tail")
    assert resp.status_code == 200
    data = resp.json()
    assert "logs" in data
    assert "total" in data
    assert isinstance(data["logs"], list)


def test_logs_entry_has_required_fields(client):
    """每条日志包含 timestamp, level, source, message"""
    _clear_log_handler()
    logging.getLogger("test.fields").warning("check fields")

    resp = client.get("/api/v1/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["logs"]) >= 1
    entry = data["logs"][-1]
    assert "timestamp" in entry
    assert "level" in entry
    assert "source" in entry
    assert "message" in entry
