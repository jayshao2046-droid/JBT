#!/usr/bin/env python3
"""研究员触发脚本 - 由 Windows 任务计划调用

职责：
1. 接收命令行参数（hour）
2. 调用本地研究员服务 API
3. 记录触发日志

使用方法：
    python trigger_researcher.py --hour 14
"""

import argparse
import httpx
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
log_dir = Path(__file__).resolve().parents[3] / "runtime" / "researcher" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "trigger.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def trigger_researcher(hour: int) -> bool:
    """
    触发研究员分析

    Args:
        hour: 小时数（0-23）

    Returns:
        True 表示触发成功
    """
    url = f"http://localhost:8199/run?hour={hour}"

    try:
        logger.info(f"触发研究员分析: hour={hour}")

        with httpx.Client(timeout=10.0) as client:
            response = client.post(url)
            response.raise_for_status()

            result = response.json()
            logger.info(f"触发成功: {result}")
            return True

    except httpx.HTTPError as e:
        logger.error(f"触发失败: {e}")
        return False

    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="触发研究员分析")
    parser.add_argument("--hour", type=int, required=True, help="小时数（0-23）")

    args = parser.parse_args()

    # 验证 hour 参数
    if not (0 <= args.hour <= 23):
        logger.error(f"无效的 hour 参数: {args.hour}（必须在 0-23 之间）")
        return 1

    # 触发研究员
    success = trigger_researcher(args.hour)

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
