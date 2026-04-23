#!/usr/bin/env python3
"""
批量调优9个策略脚本
使用三级渐进式熔断优化器对生成的策略进行调优
"""
import asyncio
import logging
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "services/decision/src"))

from research.three_tier_optimizer import ThreeTierOptimizer
from research.context_compressor import ContextCompressor
from llm.openai_client import OpenAICompatibleClient
from research.yaml_signal_executor import YAMLSignalExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🔧 批量调优9个策略")
    logger.info("="*60)

    # 加载环境变量
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / "services/decision/.env"
        load_dotenv(env_path)
        logger.info(f"✅ 已加载环境变量: {env_path}")
    except ImportError:
        logger.warning("python-dotenv 未安装，使用系统环境变量")

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

    # 初始化组件
    online_client = OpenAICompatibleClient()
    context_compressor = ContextCompressor(
        ollama_url=os.getenv("LOCAL_MODEL_BASE_URL", "http://192.168.31.142:11434")
    )
    executor = YAMLSignalExecutor(data_service_url="http://192.168.31.74:8105")

    optimizer = ThreeTierOptimizer(
        online_client=online_client,
        context_compressor=context_compressor
    )

    # 调优参数
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1年数据

    # 结果汇总
    results = []

    # 逐个调优
    for i, (strategy_file, symbol, name) in enumerate(strategies, 1):
        logger.info("")
        logger.info("="*60)
        logger.info(f"📊 [{i}/9] 调优策略: {name}")
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

            # 执行调优
            result = await optimizer.optimize(
                strategy=strategy_dict,
                executor=executor,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )

            # 保存结果
            if result.success:
                logger.info(f"✅ 调优成功")
                logger.info(f"   最终得分: {result.final_score:.4f}")
                logger.info(f"   迭代次数: {result.iterations}")
                logger.info(f"   V3调用: {result.v3_calls}, R1调用: {result.r1_calls}")
                logger.info(f"   总成本: ${result.total_cost:.4f}")

                # 保存优化后的策略
                optimized_path = strategy_path.parent / f"{strategy_path.stem}_optimized.yaml"
                with open(optimized_path, 'w', encoding='utf-8') as f:
                    yaml.dump(result.best_strategy, f, allow_unicode=True)
                logger.info(f"   已保存: {optimized_path}")

                results.append({
                    "name": name,
                    "symbol": symbol,
                    "file": strategy_file,
                    "status": "成功",
                    "final_score": result['final_score'],
                    "iterations": result['iterations'],
                    "used_r1": result['used_r1'],
                    "optimized_file": str(optimized_path)
                })
            else:
                logger.warning(f"⚠️ 调优失败: {result.get('reason', '未知原因')}")
                results.append({
                    "name": name,
                    "symbol": symbol,
                    "file": strategy_file,
                    "status": "失败",
                    "reason": result.get('reason', '未知原因')
                })

        except Exception as e:
            logger.error(f"❌ 调优异常: {e}", exc_info=True)
            results.append({
                "name": name,
                "symbol": symbol,
                "file": strategy_file,
                "status": "异常",
                "error": str(e)
            })

    # 输出汇总报告
    logger.info("")
    logger.info("="*60)
    logger.info("📊 调优汇总报告")
    logger.info("="*60)

    success_count = sum(1 for r in results if r["status"] == "成功")
    logger.info(f"总计: {len(results)} 个策略")
    logger.info(f"成功: {success_count} 个")
    logger.info(f"失败: {len(results) - success_count} 个")
    logger.info("")

    # 详细结果
    for i, result in enumerate(results, 1):
        logger.info(f"{i}. {result['name']} ({result['symbol']})")
        logger.info(f"   状态: {result['status']}")
        if result['status'] == '成功':
            logger.info(f"   得分: {result['final_score']:.4f}")
            logger.info(f"   迭代: {result['iterations']} 轮")
            logger.info(f"   R1: {'是' if result['used_r1'] else '否'}")
            logger.info(f"   文件: {result['optimized_file']}")
        elif 'reason' in result:
            logger.info(f"   原因: {result['reason']}")
        elif 'error' in result:
            logger.info(f"   错误: {result['error']}")
        logger.info("")

    # 保存 JSON 报告
    import json
    report_path = Path(__file__).parent.parent / "runtime/optimization_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": len(results),
            "success": success_count,
            "failed": len(results) - success_count,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    logger.info(f"📄 详细报告已保存: {report_path}")

    logger.info("="*60)
    logger.info("🎉 批量调优完成")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
