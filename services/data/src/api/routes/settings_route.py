"""
系统设置 API 路由
提供配置读写接口
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

# 配置文件路径
SETTINGS_PATH = Path(__file__).resolve().parents[3] / "configs" / "settings.yaml"


class NotificationConfig(BaseModel):
    feishu_webhook: str = ""
    smtp_server: str = ""
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    alert_enabled: bool = True


class SystemConfig(BaseModel):
    notifications: NotificationConfig


def _load_settings() -> Dict[str, Any]:
    """加载配置文件"""
    if not SETTINGS_PATH.exists():
        raise HTTPException(status_code=500, detail="配置文件不存在")

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_settings(config: Dict[str, Any]) -> None:
    """保存配置文件"""
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, default_flow_style=False)


@router.get("/notifications")
async def get_notifications() -> NotificationConfig:
    """获取通知配置"""
    config = _load_settings()
    monitor = config.get("monitor", {})
    feishu = monitor.get("feishu", {})
    email = monitor.get("email", {})

    return NotificationConfig(
        feishu_webhook=feishu.get("webhook_url", ""),
        smtp_server=email.get("smtp_host", ""),
        smtp_port=email.get("smtp_port", 465),
        smtp_username=email.get("username", ""),
        smtp_password=email.get("password", ""),
        alert_enabled=not feishu.get("mock_mode", False),
    )


@router.post("/notifications")
async def update_notifications(data: NotificationConfig) -> Dict[str, bool]:
    """更新通知配置"""
    config = _load_settings()

    if "monitor" not in config:
        config["monitor"] = {}
    if "feishu" not in config["monitor"]:
        config["monitor"]["feishu"] = {}
    if "email" not in config["monitor"]:
        config["monitor"]["email"] = {}

    # 更新飞书配置
    config["monitor"]["feishu"]["webhook_url"] = data.feishu_webhook
    config["monitor"]["feishu"]["mock_mode"] = not data.alert_enabled

    # 更新邮件配置
    config["monitor"]["email"]["smtp_host"] = data.smtp_server
    config["monitor"]["email"]["smtp_port"] = data.smtp_port
    config["monitor"]["email"]["username"] = data.smtp_username
    if data.smtp_password:  # 只在提供密码时更新
        config["monitor"]["email"]["password"] = data.smtp_password
    config["monitor"]["email"]["mock_mode"] = not data.alert_enabled

    _save_settings(config)
    return {"success": True}


@router.get("/health-check")
async def get_health_status() -> Dict[str, str]:
    """获取服务健康状态"""
    return {"status": "running"}
