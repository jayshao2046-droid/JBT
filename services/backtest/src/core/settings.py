from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field

SERVICE_ROOT = Path(__file__).resolve().parents[2]

# 自动加载 .env 文件（不覆盖已设置的环境变量）
_env_file = SERVICE_ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=False)


def _read_str_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer") from exc


class Settings(BaseModel):
    service_root: Path = Field(default=SERVICE_ROOT)
    service_name: str = "backtest"
    service_port: int = 8103
    log_level: str = "INFO"
    env: str = "development"
    backtest_mode: str = "online"
    data_api_url: str = "http://data:8105"
    decision_api_url: str = "http://decision:8104"
    tqsdk_edition: str = "community"
    tqsdk_account_type: str = "sim"
    tqsdk_auth_username: str = ""
    tqsdk_auth_password: str = ""
    tqsdk_strategy_yaml_dir: Path = Path("/runtime/strategies")
    backtest_storage_path: Path = Path("/runtime/backtests")
    backtest_report_path: Path = Path("/runtime/reports")
    backtest_result_dir: Path = Path("/runtime/results")
    backtest_max_concurrent: int = 2
    jwt_secret: str = ""
    jwt_expire_hours: int = 24
    api_rate_limit: int = 60
    cors_allowed: str = "http://localhost:3001"
    tushare_token: str = "<your-tushare-token>"

    @property
    def cors_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_allowed.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings(
        service_name=_read_str_env("JBT_SERVICE_NAME", "backtest"),
        service_port=_read_int_env("JBT_SERVICE_PORT", 8103),
        log_level=_read_str_env("JBT_LOG_LEVEL", "INFO"),
        env=_read_str_env("JBT_ENV", "development"),
        backtest_mode=_read_str_env("JBT_BACKTEST_MODE", "online"),
        data_api_url=_read_str_env("JBT_DATA_API_URL", "http://data:8105"),
        decision_api_url=_read_str_env("JBT_DECISION_API_URL", "http://decision:8104"),
        tqsdk_edition=_read_str_env("TQSDK_EDITION", "community"),
        tqsdk_account_type=_read_str_env("TQSDK_ACCOUNT_TYPE", "sim"),
        tqsdk_auth_username=os.getenv("TQSDK_AUTH_USERNAME", ""),
        tqsdk_auth_password=os.getenv("TQSDK_AUTH_PASSWORD", ""),
        tqsdk_strategy_yaml_dir=Path(
            _read_str_env("TQSDK_STRATEGY_YAML_DIR", "/runtime/strategies")
        ),
        backtest_storage_path=Path(
            _read_str_env("BACKTEST_STORAGE_PATH", "/runtime/backtests")
        ),
        backtest_report_path=Path(
            _read_str_env("BACKTEST_REPORT_PATH", "/runtime/reports")
        ),
        backtest_result_dir=Path(
            _read_str_env("BACKTEST_RESULT_DIR", "/runtime/results")
        ),
        backtest_max_concurrent=_read_int_env("BACKTEST_MAX_CONCURRENT", 2),
        jwt_secret=os.getenv("JBT_JWT_SECRET", ""),
        jwt_expire_hours=_read_int_env("JBT_JWT_EXPIRE_HOURS", 24),
        api_rate_limit=_read_int_env("JBT_API_RATE_LIMIT", 60),
        cors_allowed=_read_str_env("JBT_CORS_ALLOWED", "http://localhost:3001"),
        tushare_token=_read_str_env("TUSHARE_TOKEN", "<your-tushare-token>"),
    )