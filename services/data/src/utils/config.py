"""Centralized YAML configuration loader for JBT data service.

Migrated from legacy J_BotQuant/src/utils/config.py with adaptations:
- Root detection uses SERVICE_ROOT (services/data/) instead of project root
- .env lookup uses services/data/.env
- Removed feishu/email config merging (notification handled separately in A6)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from utils.exceptions import ConfigError


_SERVICE_ROOT = Path(__file__).resolve().parents[2]  # services/data/
_DEFAULT_CONFIG_PATH = _SERVICE_ROOT / "configs" / "settings.yaml"


def _read_dotenv(dotenv_path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE entries from .env into a dict."""
    if not dotenv_path.exists():
        return {}

    env_values: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_values[key.strip()] = value.strip().strip('"').strip("'")
    return env_values


def _deep_merge(target: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Merge nested dicts recursively."""
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def _apply_env_overrides(config: dict[str, Any], env_map: dict[str, str]) -> dict[str, Any]:
    """Apply sensitive env variable overrides for data sources."""
    overrides: dict[str, Any] = {
        "data_sources": {
            "tushare": {},
            "akshare": {},
        },
    }

    tushare_token = env_map.get("TUSHARE_TOKEN") or os.getenv("TUSHARE_TOKEN")
    akshare_key = env_map.get("AKSHARE_KEY") or os.getenv("AKSHARE_KEY")
    tqsdk_phone = env_map.get("TQSDK_PHONE") or os.getenv("TQSDK_PHONE")
    tqsdk_password = env_map.get("TQSDK_PASSWORD") or os.getenv("TQSDK_PASSWORD")

    if tushare_token:
        overrides["data_sources"]["tushare"]["token"] = tushare_token
    if akshare_key:
        overrides["data_sources"]["akshare"]["key"] = akshare_key
    if tqsdk_phone:
        overrides["data_sources"]["tqsdk"] = overrides["data_sources"].get("tqsdk", {})
        overrides["data_sources"]["tqsdk"]["username"] = tqsdk_phone
    if tqsdk_password:
        overrides["data_sources"]["tqsdk"] = overrides["data_sources"].get("tqsdk", {})
        overrides["data_sources"]["tqsdk"]["password"] = tqsdk_password

    # DeepSeek 翻译 API
    deepseek_key = env_map.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    deepseek_url = env_map.get("DEEPSEEK_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL")
    if deepseek_key:
        overrides["deepseek"] = {
            "api_key": deepseek_key,
            "base_url": deepseek_url or "https://api.deepseek.com/v1",
        }

    return _deep_merge(config, overrides)


def get_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from YAML and apply environment overrides.

    Raises:
        ConfigError: If the config file is missing or malformed.
    """
    final_path = Path(config_path).expanduser() if config_path else _DEFAULT_CONFIG_PATH

    if not final_path.exists():
        raise ConfigError(f"Configuration file not found: {final_path}")

    try:
        raw_content = final_path.read_text(encoding="utf-8")
        loaded = yaml.safe_load(raw_content) or {}
    except OSError as exc:
        raise ConfigError(f"Failed to read configuration file {final_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML format in {final_path}: {exc}") from exc

    if not isinstance(loaded, dict):
        raise ConfigError(f"Configuration root must be a mapping object: {final_path}")

    dotenv_values = _read_dotenv(_SERVICE_ROOT / ".env")
    return _apply_env_overrides(loaded, dotenv_values)
