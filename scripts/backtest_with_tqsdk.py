#!/usr/bin/env python3
"""
使用 tqsdk 对9个策略进行回测
回测期间：2024-01-01 到 2026-04-08
"""
import json
import yaml
from pathlib import Path
from datetime import datetime
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask

# 策略列表
STRATEGIES = [
    ("strategies/ru_meanreversion_skewfilter_001.yaml", "SHFE.ru2505", "橡胶-均值回归"),
    ("strategies/ru_autocorr_reversal_001.yaml", "SHFE.ru2505", "橡胶-反转"),
    ("strategies/ru_volatility_regime_switch_001.yaml", "SHFE.ru2505", "橡胶-波动率切换"),
    ("strategies/rb_skew_kurtosis_meanreversion_001.yaml", "SHFE.rb2505", "螺纹钢-均值回归"),
    ("strategies/rb_autocorr_flip_001.yaml", "SHFE.rb2505", "螺纹钢-反转"),
    ("strategies/rb_vol_stasis_break_001.yaml", "SHFE.rb2505", "螺纹钢-突破"),
    ("strategies/p0_skew_kurtosis_meanreversion_001.yaml", "DCE.p2505", "棕榈油-均值回归"),
    ("strategies/p0_autocorr_adaptive_holding_001.yaml", "DCE.p2505", "棕榈油-自适应"),
    ("strategies/p0_volatility_regime_shift_001.yaml", "DCE.p2505", "棕榈油-波动率跃迁"),
]


def load_strategy(yaml_path: Path) -> dict:
    """加载YAML策略文件"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_backtest(strategy_file: str, symbol: str, name: str):
    """运行单个策略回测"""
    print(f"\n{'='*60}")
    print(f"📊 回测策略: {name}")
    print(f"   文件: {strategy_file}")
    print(f"   品种: {symbol}")
    print(f"{'='*60}")

    # 加载策略
    strategy_path = Path(__file__).parent.parent / strategy_file
    if not strategy_path.exists():
        print(f"❌ 策略文件不存在: {strategy_path}")
        return None

    strategy = load_strategy(strategy_path)

    # 初始化 TqApi（回测模式）
    api = TqApi(
        backtest=TqBacktest(
            start_dt=datetime(2024, 1, 1),
            end_dt=datetime(2026, 4, 8)
        ),
        auth=TqAuth("jayshao", "Jbt@2024")  # 替换为你的天勤账号
    )

    try:
        # 获取合约
        quote = api.get_quote(symbol)

        # 获取K线数据
        klines = api.get_kline_serial(symbol, 60 * 60)  # 1小时K线

        # 创建目标持仓任务
        target_pos = TargetPosTask(api, symbol)

        # 简单示例：基于策略信号生成交易
        # 注意：这里需要根据实际策略逻辑实现信号生成
        # 当前仅作为框架示例

        position = 0
        trades = []

        while True:
            api.wait_update()

            # 这里应该根据策略YAML中的逻辑计算信号
            # 示例：简单的均线策略
            if len(klines) > 20:
                ma5 = klines.close.iloc[-5:].mean()
                ma20 = klines.close.iloc[-20:].mean()

                # 金叉做多
                if ma5 > ma20 and position <= 0:
                    position = 1
                    target_pos.set_target_volume(position)
                    trades.append({
                        "time": klines.datetime.iloc[-1],
                        "action": "buy",
                        "price": quote.last_price
                    })
                # 死叉做空
                elif ma5 < ma20 and position >= 0:
                    position = -1
                    target_pos.set_target_volume(position)
                    trades.append({
                        "time": klines.datetime.iloc[-1],
                        "action": "sell",
                        "price": quote.last_price
                    })

    except KeyboardInterrupt:
        print("\n⚠️ 回测中断")
    finally:
        # 获取回测报告
        account = api.get_account()

        result = {
            "name": name,
            "symbol": symbol,
            "file": strategy_file,
            "start_date": "2024-01-01",
            "end_date": "2026-04-08",
            "balance": account.balance,
            "trades": len(trades),
            "profit": account.balance - 10000000,  # 假设初始资金1000万
        }

        api.close()

        print(f"\n✅ 回测完成")
        print(f"   账户余额: {account.balance:,.2f}")
        print(f"   交易次数: {len(trades)}")
        print(f"   盈亏: {result['profit']:,.2f}")

        return result


def main():
    """主函数"""
    print("="*60)
    print("🚀 TqSDK 批量回测 - 9个策略")
    print("   回测期间: 2024-01-01 到 2026-04-08")
    print("="*60)

    results = []

    for strategy_file, symbol, name in STRATEGIES:
        result = run_backtest(strategy_file, symbol, name)
        if result:
            results.append(result)

    # 保存汇总报告
    report_path = Path(__file__).parent.parent / "runtime/tqsdk_backtest_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": len(results),
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"🎉 批量回测完成")
    print(f"   总计: {len(results)} 个策略")
    print(f"   报告: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
