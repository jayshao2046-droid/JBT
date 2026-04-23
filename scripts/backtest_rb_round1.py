#!/usr/bin/env python3
"""
回测单个策略：rb_volatility_breakout_001_round1.yaml
使用本地Mini数据和TQSDK数据对比
"""
import asyncio
import json
import logging
import os
import sys
import yaml
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "services/decision/src"))

from research.yaml_signal_executor import YAMLSignalExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def backtest_strategy(strategy_path: Path, data_source: str, source_name: str):
    """回测单个策略"""
    logger.info("="*80)
    logger.info(f"📊 回测策略: {strategy_path.name}")
    logger.info(f"🔧 数据源: {source_name}")
    logger.info("="*80)

    # 读取策略
    with open(strategy_path, 'r', encoding='utf-8') as f:
        strategy_dict = yaml.safe_load(f)

    # 初始化执行器
    executor = YAMLSignalExecutor(
        data_service_url=data_source,
        initial_capital=500_000.0
    )

    # 回测参数
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1年数据

    try:
        # 执行回测
        result = await executor.execute(
            strategy=strategy_dict,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            params_override=None
        )

        if result.status == "success":
            logger.info(f"✅ 回测成功")
            logger.info(f"   Sharpe比率: {result.sharpe_ratio:.4f}")
            logger.info(f"   年化收益率: {result.annualized_return:.2%}")
            logger.info(f"   最大回撤: {result.max_drawdown:.2%}")
            logger.info(f"   胜率: {result.win_rate:.2%}")
            logger.info(f"   交易次数: {result.trades_count}")
            logger.info(f"   总收益率: {result.total_return:.2%}")

            return {
                "status": "success",
                "sharpe_ratio": result.sharpe_ratio,
                "annualized_return": result.annualized_return,
                "max_drawdown": result.max_drawdown,
                "win_rate": result.win_rate,
                "trades_count": result.trades_count,
                "total_return": result.total_return,
                "start_date": result.start_date,
                "end_date": result.end_date,
            }
        else:
            logger.error(f"❌ 回测失败: {result.error}")
            return {
                "status": "failed",
                "error": result.error
            }

    except Exception as e:
        logger.error(f"❌ 回测异常: {e}", exc_info=True)
        return {
            "status": "exception",
            "error": str(e)
        }


async def main():
    """主函数"""
    logger.info("="*80)
    logger.info("🚀 回测策略: rb_volatility_breakout_001_round1.yaml")
    logger.info("="*80)

    # 加载环境变量
    try:
        from dotenv import load_dotenv
        env_path = project_root / "services/decision/.env"
        load_dotenv(env_path)
        logger.info(f"✅ 已加载环境变量")
    except ImportError:
        logger.warning("⚠️ 未安装 python-dotenv")

    # 策略文件
    strategy_path = project_root / "strategies/rb_volatility_breakout_001_round1.yaml"

    if not strategy_path.exists():
        logger.error(f"❌ 策略文件不存在: {strategy_path}")
        return

    # 1. 本地Mini数据源回测
    logger.info("\n" + "="*80)
    logger.info("阶段1：本地Mini数据源回测")
    logger.info("="*80)
    local_result = await backtest_strategy(
        strategy_path=strategy_path,
        data_source="http://192.168.31.156:8105",
        source_name="本地Mini数据服务"
    )

    # 2. TQSDK数据源回测
    logger.info("\n" + "="*80)
    logger.info("阶段2：TQSDK数据源回测")
    logger.info("="*80)

    tqsdk_url = os.getenv("TQSDK_DATA_URL", "http://localhost:8106")
    tqsdk_result = await backtest_strategy(
        strategy_path=strategy_path,
        data_source=tqsdk_url,
        source_name="TQSDK数据服务"
    )

    # 3. 生成对比报告
    logger.info("\n" + "="*80)
    logger.info("生成回测报告")
    logger.info("="*80)

    report = {
        "timestamp": datetime.now().isoformat(),
        "strategy_file": "strategies/rb_volatility_breakout_001_round1.yaml",
        "strategy_name": "螺纹钢-波动率突破-第1轮",
        "symbol": "SHFE.rb2505",
        "period": f"{(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}",
        "local_mini": {
            "data_source": "本地Mini数据服务 (http://192.168.31.156:8105)",
            **local_result
        },
        "tqsdk": {
            "data_source": f"TQSDK数据服务 ({tqsdk_url})",
            **tqsdk_result
        }
    }

    # 保存报告
    report_path = project_root / "runtime/rb_round1_backtest_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ 回测报告已保存: {report_path}")
    logger.info("")
    logger.info("="*80)
    logger.info("📊 回测结果对比")
    logger.info("="*80)

    if local_result["status"] == "success" and tqsdk_result["status"] == "success":
        logger.info(f"{'指标':<20} {'本地Mini':<20} {'TQSDK':<20}")
        logger.info("-"*80)
        logger.info(f"{'Sharpe比率':<20} {local_result['sharpe_ratio']:<20.4f} {tqsdk_result['sharpe_ratio']:<20.4f}")
        logger.info(f"{'年化收益率':<20} {local_result['annualized_return']:<20.2%} {tqsdk_result['annualized_return']:<20.2%}")
        logger.info(f"{'最大回撤':<20} {local_result['max_drawdown']:<20.2%} {tqsdk_result['max_drawdown']:<20.2%}")
        logger.info(f"{'胜率':<20} {local_result['win_rate']:<20.2%} {tqsdk_result['win_rate']:<20.2%}")
        logger.info(f"{'交易次数':<20} {local_result['trades_count']:<20} {tqsdk_result['trades_count']:<20}")

    logger.info("="*80)
    logger.info("🎉 回测完成")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(main())
