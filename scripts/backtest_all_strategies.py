#!/usr/bin/env python3
"""
回测所有策略（支持本地Mini数据和TQSDK）
生成对比报告
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


async def backtest_with_source(strategies: list, data_source: str, source_name: str):
    """使用指定数据源回测所有策略"""
    logger.info("="*80)
    logger.info(f"🔧 开始回测 - 数据源: {source_name}")
    logger.info("="*80)

    # 初始化执行器
    executor = YAMLSignalExecutor(
        data_service_url=data_source,
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
        logger.info("="*80)
        logger.info(f"📊 [{i}/{len(strategies)}] 回测策略: {name}")
        logger.info(f"    文件: {strategy_file}")
        logger.info(f"    品种: {symbol}")
        logger.info("="*80)

        try:
            # 读取策略文件
            strategy_path = project_root / strategy_file
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

    return results


async def main():
    """主函数"""
    logger.info("="*80)
    logger.info("🚀 批量回测所有策略（本地Mini + TQSDK）")
    logger.info("="*80)

    # 加载环境变量
    try:
        from dotenv import load_dotenv
        env_path = project_root / "services/decision/.env"
        load_dotenv(env_path)
        logger.info(f"✅ 已加载环境变量: {env_path}")
    except ImportError:
        logger.warning("⚠️ 未安装 python-dotenv，跳过环境变量加载")

    # 策略列表（11个策略）
    strategies = [
        # 橡胶
        ("strategies/ru_meanreversion_skewfilter_001.yaml", "SHFE.ru0", "橡胶-均值回归"),
        ("strategies/ru_autocorr_reversal_001.yaml", "SHFE.ru0", "橡胶-反转"),
        ("strategies/ru_volatility_regime_switch_001.yaml", "SHFE.ru0", "橡胶-波动率切换"),
        # 螺纹钢
        ("strategies/rb_skew_vol_break_001.yaml", "SHFE.rb0", "螺纹钢-偏度波动突破"),
        ("strategies/rb_atr_cci_adx_triple_filter_001.yaml", "SHFE.rb0", "螺纹钢-三重过滤"),
        ("strategies/rb_volatility_breakout_001.yaml", "SHFE.rb0", "螺纹钢-波动率突破"),
        ("strategies/rb_volatility_breakout_001_round1.yaml", "SHFE.rb0", "螺纹钢-波动率突破-R1"),
        ("strategies/rb_volatility_regime_001.yaml", "SHFE.rb0", "螺纹钢-波动率状态"),
        # 棕榈油
        ("strategies/p0_skew_kurtosis_meanreversion_001.yaml", "DCE.p0", "棕榈油-均值回归"),
        ("strategies/p0_autocorr_adaptive_holding_001.yaml", "DCE.p0", "棕榈油-自适应"),
        ("strategies/p0_volatility_regime_shift_001.yaml", "DCE.p0", "棕榈油-波动率跃迁"),
    ]

    # 1. 本地Mini数据源回测
    logger.info("\n" + "="*80)
    logger.info("第1阶段：本地Mini数据源回测")
    logger.info("="*80)
    local_results = await backtest_with_source(
        strategies=strategies,
        data_source="http://192.168.31.76:8105",
        source_name="本地Mini数据服务"
    )

    # 保存本地回测报告
    local_report_path = project_root / "runtime/backtest_report_local.json"
    local_report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(local_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "data_source": "本地Mini数据服务 (http://192.168.31.76:8105)",
            "period": f"{(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}",
            "total": len(local_results),
            "success": sum(1 for r in local_results if r["status"] == "success"),
            "failed": sum(1 for r in local_results if r["status"] != "success"),
            "results": local_results
        }, f, indent=2, ensure_ascii=False)

    logger.info("")
    logger.info("="*80)
    logger.info(f"✅ 本地回测完成")
    logger.info(f"   总计: {len(local_results)} 个策略")
    logger.info(f"   成功: {sum(1 for r in local_results if r['status'] == 'success')} 个")
    logger.info(f"   失败: {sum(1 for r in local_results if r['status'] != 'success')} 个")
    logger.info(f"   报告: {local_report_path}")
    logger.info("="*80)

    # 2. TQSDK数据源回测
    logger.info("\n" + "="*80)
    logger.info("第2阶段：TQSDK数据源回测")
    logger.info("="*80)

    # 检查TQSDK配置
    tqsdk_url = os.getenv("TQSDK_DATA_URL", "http://localhost:8106")
    logger.info(f"TQSDK数据源: {tqsdk_url}")

    tqsdk_results = await backtest_with_source(
        strategies=strategies,
        data_source=tqsdk_url,
        source_name="TQSDK数据服务"
    )

    # 保存TQSDK回测报告
    tqsdk_report_path = project_root / "runtime/backtest_report_tqsdk.json"

    with open(tqsdk_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "data_source": f"TQSDK数据服务 ({tqsdk_url})",
            "period": f"{(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}",
            "total": len(tqsdk_results),
            "success": sum(1 for r in tqsdk_results if r["status"] == "success"),
            "failed": sum(1 for r in tqsdk_results if r["status"] != "success"),
            "results": tqsdk_results
        }, f, indent=2, ensure_ascii=False)

    logger.info("")
    logger.info("="*80)
    logger.info(f"✅ TQSDK回测完成")
    logger.info(f"   总计: {len(tqsdk_results)} 个策略")
    logger.info(f"   成功: {sum(1 for r in tqsdk_results if r['status'] == 'success')} 个")
    logger.info(f"   失败: {sum(1 for r in tqsdk_results if r['status'] != 'success')} 个")
    logger.info(f"   报告: {tqsdk_report_path}")
    logger.info("="*80)

    # 3. 生成对比报告
    logger.info("\n" + "="*80)
    logger.info("第3阶段：生成对比报告")
    logger.info("="*80)

    comparison = []
    for i, (strategy_file, symbol, name) in enumerate(strategies):
        local_result = local_results[i]
        tqsdk_result = tqsdk_results[i]

        comparison.append({
            "name": name,
            "symbol": symbol,
            "file": strategy_file,
            "local": {
                "status": local_result.get("status"),
                "sharpe": local_result.get("sharpe_ratio"),
                "return": local_result.get("annualized_return"),
                "drawdown": local_result.get("max_drawdown"),
                "win_rate": local_result.get("win_rate"),
                "trades": local_result.get("trades_count"),
                "error": local_result.get("error")
            },
            "tqsdk": {
                "status": tqsdk_result.get("status"),
                "sharpe": tqsdk_result.get("sharpe_ratio"),
                "return": tqsdk_result.get("annualized_return"),
                "drawdown": tqsdk_result.get("max_drawdown"),
                "win_rate": tqsdk_result.get("win_rate"),
                "trades": tqsdk_result.get("trades_count"),
                "error": tqsdk_result.get("error")
            }
        })

    # 保存对比报告
    comparison_report_path = project_root / "runtime/backtest_comparison.json"

    with open(comparison_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "period": f"{(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}",
            "total": len(strategies),
            "local_success": sum(1 for r in local_results if r["status"] == "success"),
            "tqsdk_success": sum(1 for r in tqsdk_results if r["status"] == "success"),
            "comparison": comparison
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ 对比报告已生成: {comparison_report_path}")
    logger.info("")
    logger.info("="*80)
    logger.info("🎉 所有回测完成")
    logger.info("="*80)
    logger.info(f"📊 报告文件:")
    logger.info(f"   - 本地回测: {local_report_path}")
    logger.info(f"   - TQSDK回测: {tqsdk_report_path}")
    logger.info(f"   - 对比报告: {comparison_report_path}")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(main())
