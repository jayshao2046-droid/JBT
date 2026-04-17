#!/usr/bin/env python3
"""费用摘要 Cron 任务脚本 — TASK-U0-20260417-004

每小时整点运行，发送费用摘要到飞书看板。

使用方式:
1. 配置环境变量（.env）
2. 添加到 crontab:
   0 * * * * cd /Users/jayshao/JBT && python scripts/send_cost_summary.py

输出:
- 飞书看板卡片
- 日志: logs/cost_summary.log
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.monitoring.cost_tracker import APIUsageTracker

# 配置日志
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'cost_summary.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("📊 发送费用摘要（Cron 任务）")

    try:
        # 加载环境变量
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).parent.parent / "services/decision/.env"
            load_dotenv(env_path)
        except ImportError:
            logger.warning("python-dotenv 未安装，使用系统环境变量")

        # 初始化成本追踪器
        cost_tracker = APIUsageTracker(
            daily_budget=float(os.getenv("DAILY_API_BUDGET", "10.0")),
            feishu_webhook_url=os.getenv("FEISHU_WEBHOOK_URL")
        )

        # 发送每小时费用摘要
        await cost_tracker.send_hourly_report()

        logger.info("✅ 费用摘要发送成功")

    except Exception as e:
        logger.error(f"❌ 费用摘要发送失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
