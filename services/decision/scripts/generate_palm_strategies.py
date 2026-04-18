#!/usr/bin/env python3
"""棕榈油策略生成与双回测验证流程

功能：
1. 使用 SymbolProfiler 分析棕榈油特征
2. 使用 StrategyArchitect 设计3个不同趋势策略
3. 使用 CodeGenerator 生成 YAML 策略文件
4. 使用 YAMLSignalExecutor 进行沙箱回测
5. 使用 TqSDK 进行真实回测验证
6. 生成完整的双回测对比报告

用法：
    cd /Users/jayshao/JBT/services/decision
    source ../../.venv/bin/activate
    python scripts/generate_palm_strategies.py
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
_BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE))

# 加载 .env 文件
from dotenv import load_dotenv
_ENV_PATH = _BASE.parent.parent / ".env"  # /Users/jaybot/JBT/.env
load_dotenv(_ENV_PATH)

from src.research.symbol_profiler import SymbolProfiler
from src.research.strategy_architect import StrategyArchitect
from src.research.code_generator import CodeGenerator
from src.research.yaml_signal_executor import YAMLSignalExecutor
from src.llm.openai_client import OpenAICompatibleClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("palm_strategy_generator")

# 配置
SYMBOL = "SHFE.rb0"  # 螺纹钢主力合约（测试用，棕榈油数据暂缺）
SYMBOL_NAME = "rb"
START_DATE = "2023-01-01"
END_DATE = "2025-12-31"
DATA_URL = "http://192.168.31.76:8105"
OLLAMA_URL = "http://192.168.31.142:11434"

# 在线模型配置（通义千问）
ONLINE_BASE_URL = os.getenv("ONLINE_MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
ONLINE_API_KEY = os.getenv("ONLINE_MODEL_API_KEY", "")

# 输出目录
OUTPUT_DIR = _BASE / "runtime" / "palm_strategies"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REPORTS_DIR = OUTPUT_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


async def generate_strategies():
    """生成3个棕榈油趋势策略"""

    logger.info("=" * 80)
    logger.info("棕榈油策略生成与双回测验证流程")
    logger.info("=" * 80)
    logger.info(f"品种: {SYMBOL} ({SYMBOL_NAME})")
    logger.info(f"回测区间: {START_DATE} ~ {END_DATE}")
    logger.info(f"输出目录: {OUTPUT_DIR}")
    logger.info("")

    # 初始化客户端
    logger.info("🔧 初始化组件...")
    online_client = OpenAICompatibleClient(
        base_url=ONLINE_BASE_URL,
        api_key=ONLINE_API_KEY
    )

    # 第一步：品种特征分析
    logger.info("")
    logger.info("=" * 80)
    logger.info("第一步：品种特征分析 (SymbolProfiler)")
    logger.info("=" * 80)

    profiler = SymbolProfiler(
        data_service_url=DATA_URL
    )

    profile = await profiler.calculate_features(
        symbol=SYMBOL
    )

    logger.info(f"✅ 品种特征分析完成")
    logger.info(f"   波动率: {profile.get('volatility', 'N/A')}")
    logger.info(f"   趋势性: {profile.get('trend_strength', 'N/A')}")
    logger.info(f"   推荐因子: {profile.get('recommended_factors', [])}")

    # 保存品种特征
    profile_path = OUTPUT_DIR / f"{SYMBOL_NAME}_profile.json"
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    logger.info(f"   特征报告: {profile_path}")

    # 第二步：策略设计
    logger.info("")
    logger.info("=" * 80)
    logger.info("第二步：策略设计 (StrategyArchitect)")
    logger.info("=" * 80)

    architect = StrategyArchitect(
        online_client=online_client,
        model="deepseek-chat"  # 使用 DeepSeek V3
    )

    # 设计3个不同趋势策略
    strategy_types = [
        {
            "name": "短期趋势跟踪",
            "description": "基于5分钟K线的短期趋势捕捉，使用MACD+RSI组合",
            "timeframe": 5,
            "style": "trend_following"
        },
        {
            "name": "中期趋势突破",
            "description": "基于30分钟K线的中期趋势突破，使用ATR+ADX组合",
            "timeframe": 30,
            "style": "breakout"
        },
        {
            "name": "长期趋势持有",
            "description": "基于120分钟K线的长期趋势持有，使用均线+波动率组合",
            "timeframe": 120,
            "style": "trend_following"
        }
    ]

    strategy_designs = []
    for i, strategy_type in enumerate(strategy_types, 1):
        logger.info(f"\n设计策略 {i}/3: {strategy_type['name']}")

        design = await architect.design_strategy(
            symbol_profile=profile,
            strategy_type=strategy_type['style'],
            timeframe=strategy_type['timeframe']
        )

        if design:
            design['strategy_name'] = f"{SYMBOL_NAME}_{strategy_type['style']}_{strategy_type['timeframe']}m_v1"
            design['description'] = strategy_type['description']
            strategy_designs.append(design)
            logger.info(f"   ✅ 策略设计完成: {design['strategy_name']}")
        else:
            logger.warning(f"   ❌ 策略设计失败")

    if not strategy_designs:
        logger.error("所有策略设计都失败，退出")
        return

    # 第三步：代码生成
    logger.info("")
    logger.info("=" * 80)
    logger.info("第三步：代码生成 (CodeGenerator)")
    logger.info("=" * 80)

    generator = CodeGenerator(
        online_client=online_client,
        model="qwen-coder-plus",
        output_dir=str(OUTPUT_DIR)
    )

    generated_strategies = []
    for i, design in enumerate(strategy_designs, 1):
        logger.info(f"\n生成策略 {i}/{len(strategy_designs)}: {design['strategy_name']}")

        yaml_path = await generator.generate_yaml_strategy(
            strategy_design=design,
            symbol=SYMBOL,
            timeframe=design.get('timeframe', 120)
        )

        if yaml_path:
            generated_strategies.append({
                'design': design,
                'yaml_path': yaml_path
            })
            logger.info(f"   ✅ YAML 生成完成: {yaml_path}")
        else:
            logger.warning(f"   ❌ YAML 生成失败")

    if not generated_strategies:
        logger.error("所有策略生成都失败，退出")
        return

    # 第四步：沙箱回测
    logger.info("")
    logger.info("=" * 80)
    logger.info("第四步：沙箱回测 (YAMLSignalExecutor)")
    logger.info("=" * 80)

    executor = YAMLSignalExecutor(
        data_service_url=DATA_URL,
        ollama_url=OLLAMA_URL
    )

    backtest_results = []
    for i, strategy_info in enumerate(generated_strategies, 1):
        yaml_path = strategy_info['yaml_path']
        strategy_name = strategy_info['design']['strategy_name']

        logger.info(f"\n回测策略 {i}/{len(generated_strategies)}: {strategy_name}")

        # 读取 YAML
        import yaml
        with open(yaml_path, "r", encoding="utf-8") as f:
            strategy = yaml.safe_load(f)

        # 执行回测
        result = await executor.execute(strategy, START_DATE, END_DATE)

        if result.status == "success":
            logger.info(f"   ✅ 回测完成")
            logger.info(f"      Sharpe: {result.sharpe_ratio:.4f}")
            logger.info(f"      最大回撤: {result.max_drawdown * 100:.2f}%")
            logger.info(f"      胜率: {result.win_rate * 100:.2f}%")
            logger.info(f"      年化收益: {result.annualized_return * 100:.2f}%")
            logger.info(f"      交易次数: {result.trades_count}")

            backtest_results.append({
                'strategy_name': strategy_name,
                'yaml_path': str(yaml_path),
                'sandbox_result': result.to_dict(),
                'passed': result.sharpe_ratio >= 0.5 and result.trades_count >= 10
            })
        else:
            logger.warning(f"   ❌ 回测失败: {result.error}")
            backtest_results.append({
                'strategy_name': strategy_name,
                'yaml_path': str(yaml_path),
                'sandbox_result': {'error': result.error},
                'passed': False
            })

    # 第五步：生成报告
    logger.info("")
    logger.info("=" * 80)
    logger.info("第五步：生成报告")
    logger.info("=" * 80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        'symbol': SYMBOL,
        'symbol_name': SYMBOL_NAME,
        'start_date': START_DATE,
        'end_date': END_DATE,
        'timestamp': timestamp,
        'profile': profile,
        'strategies': backtest_results,
        'summary': {
            'total': len(backtest_results),
            'passed': sum(1 for r in backtest_results if r['passed']),
            'failed': sum(1 for r in backtest_results if not r['passed'])
        }
    }

    report_path = REPORTS_DIR / f"palm_strategies_{timestamp}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 报告已保存: {report_path}")

    # 打印汇总
    logger.info("")
    logger.info("=" * 80)
    logger.info("汇总报告")
    logger.info("=" * 80)
    logger.info(f"总计: {report['summary']['total']} 个策略")
    logger.info(f"通过: {report['summary']['passed']} 个 ✅")
    logger.info(f"失败: {report['summary']['failed']} 个 ❌")
    logger.info("")

    for i, result in enumerate(backtest_results, 1):
        status = "✅" if result['passed'] else "❌"
        sandbox = result.get('sandbox_result', {})
        sharpe = sandbox.get('sharpe_ratio', 0)
        trades = sandbox.get('trades_count', 0)
        logger.info(f"{i}. {result['strategy_name']} {status}")
        logger.info(f"   Sharpe: {sharpe:.4f} | 交易次数: {trades}")

    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ 策略生成与回测完成！")
    logger.info("=" * 80)
    logger.info(f"策略文件: {OUTPUT_DIR}")
    logger.info(f"回测报告: {report_path}")
    logger.info("")
    logger.info("下一步：")
    logger.info("1. 查看回测报告，确认策略质量")
    logger.info("2. 对通过的策略执行 TqSDK 真实回测验证")
    logger.info("3. 保留双回测报告供查阅")

    await online_client.close()


if __name__ == "__main__":
    if not ONLINE_API_KEY:
        logger.error("❌ 缺少 ONLINE_MODEL_API_KEY 环境变量")
        logger.error("请设置通义千问 API Key:")
        logger.error("export ONLINE_MODEL_API_KEY='your-api-key'")
        sys.exit(1)

    asyncio.run(generate_strategies())
