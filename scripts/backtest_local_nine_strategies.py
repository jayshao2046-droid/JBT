#!/usr/bin/env python3
"""
本地回测9个策略（使用Mini数据服务）
生成回测报告作为策略调优完成证据
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
sys.path.insert(0, str(project_root / "services/decision/src"))

from research.yaml_signal_executor import YAMLSignalExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🔧 本地回测9个策略（Mini数据服务）")
    logger.info("="*60)

    # 加载环境变量
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / "services/decision/.env"
        load_dotenv(env_path)
        logger.info(f"✅ 已加载环境变量: {env_path}")
    except ImportError:
        logger.warning("⚠️ 未安装 python-dotenv，跳过环境变量加载")

    # 策略列表
    strategies = [
        # 橡胶
        ("strategies/ru_meanreversion_skewfilter_001.yaml", "SHFE.ru0", "橡胶-均值回归"),
        ("strategies/ru_autocorr_reversal_001.yaml", "SHFE.ru0", "橡胶-反转"),
        ("strategies/ru_volatility_regime_switch_001.yaml", "SHFE.ru0", "橡胶-波动率切换"),
        # 螺纹钢
        ("strategies/rb_skew_kurtosis_meanreversion_001.yaml", "SHFE.rb0", "螺纹钢-均值回归"),
        ("strategies/rb_autocorr_flip_001.yaml", "SHFE.rb0", "螺纹钢-反转"),
        ("strategies/rb_vol_stasis_break_001.yaml", "SHFE.rb0", "螺纹钢-突破"),
        # 棕榈油
        ("strategies/p0_skew_kurtosis_meanreversion_001.yaml", "DCE.p0", "棕榈油-均值回归"),
        ("strategies/p0_autocorr_adaptive_holding_001.yaml", "DCE.p0", "棕榈油-自适应"),
        ("strategies/p0_volatility_regime_shift_001.yaml", "DCE.p0", "棕榈油-波动率跃迁"),
    ]

    # 初始化执行器
    executor = YAMLSignalExecutor(
        data_service_url="http://192.168.31.156:8105",
        initial_capital=500_000.0
    )

    # 回测参数
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1年数据

    # 结果汇总
    results = []

    # 逐个回测
    for i, (strategy_file, symbol, name) in enumerate(strategies, 1):
        logger.info("")
        logger.info("="*60)
        logger.info(f"📊 [{i}/9] 回测策略: {name}")
        logger.info(f"    文件: {strategy_file}")
        logger.info(f"    品种: {symbol}")
        logger.info("="*60)

        try:
            # 读取策略文件
            strategy_path = Path(__file__).parent.parent / strategy_file
            if not strategy_path.exists():
                logger.error(f"❌ 策略文件不存在: {strategy_path}")
                results.append({
                    "name": name,
                    "symbol": symbol,
                    "file": strategy_file,
                    "status": "文件不存在",
                    "error": "策略文件不存在"
                })
                continue

            with open(strategy_path, 'r', encoding='utf-8') as f:
                strategy_dict = yaml.safe_load(f)

            # 确保策略中有正确的symbol
            if 'symbol' not in strategy_dict:
                strategy_dict['symbol'] = symbol

            # 执行回测
            result = await executor.execute(
                strategy=strategy_dict,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                params_override=None
            )

            # 保存结果
            if result.status == "success":
                logger.info(f"✅ 回测成功")
                logger.info(f"   Sharpe: {result.sharpe_ratio:.4f}")
                logger.info(f"   年化收益: {result.annualized_return:.2%}")
                logger.info(f"   最大回撤: {result.max_drawdown:.2%}")
                logger.info(f"   胜率: {result.win_rate:.2%}")
                logger.info(f"   交易次数: {result.trades_count}")

                results.append({
                    "name": name,
                    "symbol": symbol,
                    "file": strategy_file,
                    "status": "success",
                    "sharpe_ratio": result.sharpe_ratio,
                    "annualized_return": result.annualized_return,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "trades_count": result.trades_count,
                    "total_return": result.total_return,
                    "start_date": result.start_date,
                    "end_date": result.end_date,
                })
            else:
                logger.error(f"❌ 回测失败: {result.error}")
                results.append({
                    "name": name,
                    "symbol": symbol,
                    "file": strategy_file,
                    "status": "failed",
                    "error": result.error
                })

        except Exception as e:
            logger.error(f"❌ 回测异常: {e}", exc_info=True)
            results.append({
                "name": name,
                "symbol": symbol,
                "file": strategy_file,
                "status": "exception",
                "error": str(e)
            })

    # 保存汇总报告
    report_path = Path(__file__).parent.parent / "runtime/local_backtest_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "data_source": "Mini数据服务 (http://192.168.31.156:8105)",
            "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
            "total": len(results),
            "success": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] != "success"),
            "results": results
        }, f, indent=2, ensure_ascii=False)

    logger.info("")
    logger.info("="*60)
    logger.info(f"🎉 本地回测完成")
    logger.info(f"   总计: {len(results)} 个策略")
    logger.info(f"   成功: {sum(1 for r in results if r['status'] == 'success')} 个")
    logger.info(f"   失败: {sum(1 for r in results if r['status'] != 'success')} 个")
    logger.info(f"   报告: {report_path}")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
