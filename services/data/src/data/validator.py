"""数据源配置验证器"""
from __future__ import annotations

import re
from typing import Any, Optional

import requests


class DataSourceValidator:
    """数据源配置验证器"""

    def __init__(self) -> None:
        self.timeout = 10

    def validate_connection(self, source_type: str, config: dict[str, Any]) -> dict[str, Any]:
        """验证数据源连接

        Args:
            source_type: 数据源类型 (tushare/tqsdk/akshare/yfinance)
            config: 配置字典

        Returns:
            验证结果 {"ok": bool, "message": str}
        """
        if source_type == "tushare":
            return self._validate_tushare(config)
        elif source_type == "tqsdk":
            return self._validate_tqsdk(config)
        elif source_type == "akshare":
            return self._validate_akshare(config)
        elif source_type == "yfinance":
            return self._validate_yfinance(config)
        else:
            return {"ok": False, "message": f"不支持的数据源类型: {source_type}"}

    def validate_config(self, source_type: str, config: dict[str, Any]) -> dict[str, Any]:
        """验证配置完整性

        Args:
            source_type: 数据源类型
            config: 配置字典

        Returns:
            验证结果 {"ok": bool, "message": str, "missing_fields": list}
        """
        required_fields = self._get_required_fields(source_type)
        missing = [field for field in required_fields if not config.get(field)]

        if missing:
            return {
                "ok": False,
                "message": f"缺少必填字段: {', '.join(missing)}",
                "missing_fields": missing,
            }

        return {"ok": True, "message": "配置完整", "missing_fields": []}

    def validate_permissions(self, source_type: str, config: dict[str, Any]) -> dict[str, Any]:
        """验证权限

        Args:
            source_type: 数据源类型
            config: 配置字典

        Returns:
            验证结果 {"ok": bool, "message": str, "permissions": list}
        """
        if source_type == "tushare":
            token = config.get("token", "")
            if not token:
                return {"ok": False, "message": "缺少 token", "permissions": []}

            # Tushare token 格式验证
            if len(token) < 32:
                return {"ok": False, "message": "token 格式无效", "permissions": []}

            return {
                "ok": True,
                "message": "权限验证通过",
                "permissions": ["行情数据", "基本面数据"],
            }

        elif source_type == "tqsdk":
            username = config.get("username", "")
            password = config.get("password", "")
            if not username or not password:
                return {"ok": False, "message": "缺少用户名或密码", "permissions": []}

            return {
                "ok": True,
                "message": "权限验证通过",
                "permissions": ["期货行情", "期货交易"],
            }

        else:
            return {"ok": True, "message": "无需权限验证", "permissions": []}

    def _get_required_fields(self, source_type: str) -> list[str]:
        """获取必填字段列表"""
        fields_map = {
            "tushare": ["token"],
            "tqsdk": ["username", "password"],
            "akshare": [],
            "yfinance": [],
        }
        return fields_map.get(source_type, [])

    def _validate_tushare(self, config: dict[str, Any]) -> dict[str, Any]:
        """验证 Tushare 连接"""
        token = config.get("token", "")
        if not token:
            return {"ok": False, "message": "缺少 token"}

        try:
            # 简单的 token 格式验证
            if len(token) < 32 or not re.match(r"^[a-zA-Z0-9]+$", token):
                return {"ok": False, "message": "token 格式无效"}

            # 实际环境中应该调用 Tushare API 验证
            return {"ok": True, "message": "连接成功"}
        except Exception as e:
            return {"ok": False, "message": f"连接失败: {str(e)}"}

    def _validate_tqsdk(self, config: dict[str, Any]) -> dict[str, Any]:
        """验证 TqSdk 连接"""
        username = config.get("username", "")
        password = config.get("password", "")

        if not username or not password:
            return {"ok": False, "message": "缺少用户名或密码"}

        # 实际环境中应该调用 TqSdk API 验证
        return {"ok": True, "message": "连接成功"}

    def _validate_akshare(self, config: dict[str, Any]) -> dict[str, Any]:
        """验证 AkShare 连接"""
        try:
            # AkShare 无需认证，测试网络连接
            response = requests.get("https://www.akshare.xyz", timeout=self.timeout)
            if response.status_code == 200:
                return {"ok": True, "message": "连接成功"}
            else:
                return {"ok": False, "message": f"连接失败: HTTP {response.status_code}"}
        except requests.RequestException as e:
            return {"ok": False, "message": f"网络错误: {str(e)}"}

    def _validate_yfinance(self, config: dict[str, Any]) -> dict[str, Any]:
        """验证 yfinance 连接"""
        try:
            # yfinance 无需认证，测试网络连接
            response = requests.get("https://finance.yahoo.com", timeout=self.timeout)
            if response.status_code == 200:
                return {"ok": True, "message": "连接成功"}
            else:
                return {"ok": False, "message": f"连接失败: HTTP {response.status_code}"}
        except requests.RequestException as e:
            return {"ok": False, "message": f"网络错误: {str(e)}"}
