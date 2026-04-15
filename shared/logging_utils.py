"""
共享日志工具 - 敏感信息过滤

P2-3 修复：实现日志敏感信息过滤，防止凭证、Token、密码等泄露到日志文件
"""
import re
import logging
from typing import Any


class SensitiveDataFilter(logging.Filter):
    """
    日志过滤器：自动脱敏敏感信息

    使用方法：
        logger = logging.getLogger(__name__)
        logger.addFilter(SensitiveDataFilter())
    """

    # 敏感字段名称模式（不区分大小写）
    SENSITIVE_KEYS = [
        'password', 'passwd', 'pwd',
        'secret', 'token', 'api_key', 'apikey',
        'auth', 'authorization', 'credential',
        'private_key', 'access_key', 'session',
        'cookie', 'jwt', 'bearer',
    ]

    # 敏感值模式（正则表达式）
    SENSITIVE_PATTERNS = [
        # API Keys (通常是长字符串)
        (re.compile(r'\b[A-Za-z0-9_-]{32,}\b'), '***API_KEY***'),
        # JWT Tokens
        (re.compile(r'\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b'), '***JWT_TOKEN***'),
        # 密码字段 (key=value 或 "key": "value" 格式)
        (re.compile(r'(password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***'),
        # Authorization header
        (re.compile(r'(Authorization|X-API-Key)\s*:\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1: ***'),
        # 环境变量格式 (KEY=value)
        (re.compile(r'([A-Z_]+(?:TOKEN|KEY|SECRET|PASSWORD))\s*=\s*([^\s]+)', re.IGNORECASE), r'\1=***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录，脱敏敏感信息

        Args:
            record: 日志记录对象

        Returns:
            True (始终允许日志通过，但会修改内容)
        """
        # 过滤消息内容
        if isinstance(record.msg, str):
            record.msg = self._sanitize_string(record.msg)

        # 过滤参数
        if record.args:
            record.args = self._sanitize_args(record.args)

        return True

    def _sanitize_string(self, text: str) -> str:
        """脱敏字符串中的敏感信息"""
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    def _sanitize_args(self, args: Any) -> Any:
        """脱敏日志参数"""
        if isinstance(args, dict):
            return {k: self._sanitize_value(k, v) for k, v in args.items()}
        elif isinstance(args, (list, tuple)):
            return type(args)(self._sanitize_value(None, item) for item in args)
        else:
            return self._sanitize_value(None, args)

    def _sanitize_value(self, key: str | None, value: Any) -> Any:
        """脱敏单个值"""
        # 检查键名是否敏感
        if key and any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
            return '***'

        # 递归处理嵌套结构
        if isinstance(value, dict):
            return {k: self._sanitize_value(k, v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return type(value)(self._sanitize_value(None, item) for item in value)
        elif isinstance(value, str):
            return self._sanitize_string(value)
        else:
            return value


def setup_logger_with_filter(logger: logging.Logger) -> None:
    """
    为 logger 添加敏感信息过滤器

    Args:
        logger: 要配置的 logger 对象
    """
    logger.addFilter(SensitiveDataFilter())


# 示例用法
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # 添加过滤器
    setup_logger_with_filter(logger)

    # 测试
    logger.info("User login with password=secret123")  # 会被脱敏
    logger.info("API request with X-API-Key: sk_live_1234567890abcdef")  # 会被脱敏
    logger.info("JWT token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U")  # 会被脱敏
    logger.info("Normal log message")  # 不会被修改
