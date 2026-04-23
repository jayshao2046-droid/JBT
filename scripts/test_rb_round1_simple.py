#!/usr/bin/env python3
"""简单测试rb_round1策略"""
import asyncio
import sys
import yaml
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "services/decision/src"))

from research.yaml_signal_executor import YAMLSignalExecutor

async def main():
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        env_path = project_root / "services/decision/.env"
        load_dotenv(env_path)
        print(f"✅ 已加载环境变量")
    except ImportError:
        print("⚠️ 未安装 python-dotenv")

    # 读取策略
    strategy_path = project_root / "strategies/rb_volatility_breakout_001_round1.yaml"
    with open(strategy_path, 'r', encoding='utf-8') as f:
        strategy = yaml.safe_load(f)

    print(f"策略名称: {strategy['name']}")
    print(f"品种: {strategy.get('symbols', strategy.get('symbol', 'N/A'))}")

    # 初始化执行器
    executor = YAMLSignalExecutor(
        data_service_url="http://192.168.31.74:8105",
        initial_capital=500_000.0
    )

    # 回测
    end_date = datetime(2026, 4, 8)  # 与文档一致
    start_date = datetime(2024, 1, 1)  # 与文档一致

    print(f"\n开始回测: {start_date.date()} 至 {end_date.date()}")

    result = await executor.execute(
        strategy=strategy,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        params_override=None
    )

    print(f"\n回测状态: {result.status}")
    if result.status == "success":
        print(f"Sharpe: {result.sharpe_ratio:.4f}")
        print(f"年化收益: {result.annualized_return:.2%}")
        print(f"最大回撤: {result.max_drawdown:.2%}")
        print(f"胜率: {result.win_rate:.2%}")
        print(f"交易次数: {result.trades_count}")
    else:
        print(f"错误: {result.error}")
        # 打印更多调试信息
        import traceback
        if hasattr(result, '__dict__'):
            print(f"\n完整结果对象:")
            for k, v in result.__dict__.items():
                if k != 'error':
                    print(f"  {k}: {v}")

if __name__ == "__main__":
    asyncio.run(main())
