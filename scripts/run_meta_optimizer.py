#!/usr/bin/env python3
"""元优化器 Cron 任务脚本 — TASK-U0-20260417-004

每月1号凌晨2点自动运行，进化参数映射规则。

使用方式:
1. 配置环境变量（.env）
2. 添加到 crontab:
   0 2 1 * * cd /Users/jayshao/JBT && python scripts/run_meta_optimizer.py

输出:
- 进化报告: runtime/optimization_history/meta_optimization_report_YYYYMMDD.json
- 新规则: runtime/param_mapping_rules_review_YYYYMMDD_HHMMSS.yaml
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.meta_optimizer import MetaOptimizer
from services.decision.src.llm.openai_client import OpenAICompatibleClient

# 配置日志
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'meta_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🧬 启动参数规则自我进化（Cron 任务）")
    logger.info("="*60)

    try:
        # 加载环境变量
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).parent.parent / "services/decision/.env"
            load_dotenv(env_path)
        except ImportError:
            logger.warning("python-dotenv 未安装，使用系统环境变量")

        # 初始化客户端
        online_client = OpenAICompatibleClient()

        # 初始化元优化器
        meta_optimizer = MetaOptimizer(
            online_client=online_client,
            rules_path="./runtime/param_mapping_rules.yaml",
            history_dir="./runtime/optimization_history"
        )

        # 进化规则（回溯30天）
        report = await meta_optimizer.evolve_rules(days=30)

        # 输出报告
        logger.info("\n" + "="*60)
        logger.info("📊 进化报告")
        logger.info("="*60)
        logger.info(f"成功: {report['success']}")
        logger.info(f"收集记录: {report.get('records_count', 0)} 条")
        logger.info(f"高质量记录: {report.get('high_quality_count', 0)} 条")

        if report['success']:
            logger.info(f"新规则路径: {report['new_rules_path']}")
            logger.info("\n⚠️ 请人工审核后，运行以下命令批准新规则:")
            logger.info(f"python scripts/approve_rules.py {report['new_rules_path']}")
        else:
            logger.warning(f"进化失败: {report.get('reason', '未知原因')}")

        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ 元优化器运行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
