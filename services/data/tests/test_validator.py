"""数据源验证器测试"""
from __future__ import annotations

import pytest

from src.data.validator import DataSourceValidator


def test_validate_tushare_connection():
    validator = DataSourceValidator()
    config = {"token": "a" * 32}
    result = validator.validate_connection("tushare", config)
    assert result["ok"] is True


def test_validate_tushare_invalid_token():
    validator = DataSourceValidator()
    config = {"token": "short"}
    result = validator.validate_connection("tushare", config)
    assert result["ok"] is False


def test_validate_tqsdk_connection():
    validator = DataSourceValidator()
    config = {"username": "test", "password": "test123"}
    result = validator.validate_connection("tqsdk", config)
    assert result["ok"] is True


def test_validate_config_tushare():
    validator = DataSourceValidator()
    config = {"token": "test_token"}
    result = validator.validate_config("tushare", config)
    assert result["ok"] is True


def test_validate_config_missing_fields():
    validator = DataSourceValidator()
    config = {}
    result = validator.validate_config("tushare", config)
    assert result["ok"] is False
    assert "token" in result["missing_fields"]


def test_validate_permissions_tushare():
    validator = DataSourceValidator()
    config = {"token": "a" * 32}
    result = validator.validate_permissions("tushare", config)
    assert result["ok"] is True
    assert len(result["permissions"]) > 0


def test_validate_permissions_tqsdk():
    validator = DataSourceValidator()
    config = {"username": "test", "password": "test123"}
    result = validator.validate_permissions("tqsdk", config)
    assert result["ok"] is True


def test_validate_unsupported_source():
    validator = DataSourceValidator()
    config = {}
    result = validator.validate_connection("unknown", config)
    assert result["ok"] is False
