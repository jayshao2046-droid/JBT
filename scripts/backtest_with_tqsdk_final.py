"""使用tqsdk进行标准回测验证

在本地回测达标后，使用tqsdk进行标准回测验证。
回测期间：2024-01-01 到 2026-04-08
天勤账号：17621181300 / Jay.486858
"""
import asyncio
import json
import logging
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "services" / "decision" / ".env")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from tqsdk import TqApi, TqAuth, TqSim, BacktestFinished
    from tqsdk.ta import ATR, ADX, RSI, MACD, CCI
    TQSDK_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ tqsdk未安装，请运行: pip install tqsdk")
    TQSDK_AVAILABLE = False


class TqsdkBacktester:
    """tqsdk回测器"""

    def __init__(self, username: str = "17621181300", password: str = "Jay.486858"):
        self.username = username
        self.password = password

    async def backtest_strategy(
        self,
        yaml_path: str,
        start_date: str = "2024-01-01",
        end_date: str = "2026-04-08"
    ) -> dict:
        """执行tqsdk回测"""
        if not TQSDK_AVAILABLE:
            return {
                "success": False,
                "error": "tqsdk未安装"
            }

        logger.info("=" * 60)
        logger.info("tqsdk标准回测")
        logger.info("=" * 60)

        # 读取策略配置
        with open(yaml_path, 'r', encoding='utf-8') as f:
            strategy = yaml.safe_load(f)

        symbol = strategy.get('symbols', ['SHFE.rb2505'])[0]
        logger.info(f"品种：{symbol}")
        logger.info(f"回测期间：{start_date} ~ {end_date}")

        # 转换为主力合约
        main_symbol = self._get_main_contract(symbol)
        logger.info(f"主力合约：{main_symbol}")

        try:
            # 初始化API
            api = TqApi(
                auth=TqAuth(self.username, self.password),
                backtest={
                    "start_dt": datetime.strptime(start_date, "%Y-%m-%d"),
                    "end_dt": datetime.strptime(end_date, "%Y-%m-%d")
                }
            )

            # 获取K线数据
            klines = api.get_kline_serial(main_symbol, duration_seconds=strategy.get('timeframe_minutes', 120) * 60)

            # 计算因子
            factors = self._calculate_factors(api, klines, strategy.get('factors', []))

            # 执行回测逻辑
            result = self._run_backtest_logic(api, klines, factors, strategy)

            api.close()

            logger.info("✅ tqsdk回测完成")
            return result

        except BacktestFinished:
            logger.info("✅ 回测结束")
            return self._extract_results(api)
        except Exception as e:
            logger.error(f"❌ tqsdk回测失败：{e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_main_contract(self, symbol: str) -> str:
        """获取主力合约"""
        # 简化处理：直接使用KQ.m@符号
        if '.' in symbol:
            exchange, contract = symbol.split('.')
            # 提取品种代码（如rb2505 -> rb）
            product = ''.join([c for c in contract if not c.isdigit()])
            return f"KQ.m@{exchange}.{product}"
        return symbol

    def _calculate_factors(self, api, klines, factor_configs: list) -> dict:
        """计算因子"""
        factors = {}

        for config in factor_configs:
            factor_name = config.get('factor_name', '')
            params = config.get('params', {})

            if factor_name == 'ATR':
                period = params.get('period', 14)
                factors['atr'] = ATR(klines, period)
            elif factor_name == 'ADX':
                period = params.get('period', 14)
                factors['adx'] = ADX(klines, period)
            elif factor_name == 'RSI':
                period = params.get('period', 14)
                factors['rsi'] = RSI(klines, period)
            elif factor_name == 'CCI':
                period = params.get('period', 20)
                factors['cci'] = CCI(klines, period)
            elif factor_name == 'MACD':
                fast = params.get('fast', 12)
                slow = params.get('slow', 26)
                signal = params.get('signal', 9)
                factors['macd'] = MACD(klines, fast, slow, signal)

        return factors

    def _run_backtest_logic(self, api, klines, factors: dict, strategy: dict) -> dict:
        """执行回测逻辑"""
        # 获取信号条件
        signal = strategy.get('signal', {})
        long_condition = signal.get('long_condition', '')
        short_condition = signal.get('short_condition', '')

        # 统计信息
        trades = []
        position = 0

        # 遍历K线
        for i in range(len(klines)):
            # 构建评估环境
            env = {
                'close': klines.close.iloc[i],
                'open': klines.open.iloc[i],
                'high': klines.high.iloc[i],
                'low': klines.low.iloc[i],
                'volume': klines.volume.iloc[i],
            }

            # 添加因子值
            for name, series in factors.items():
                if hasattr(series, 'iloc'):
                    env[name] = series.iloc[i]
                else:
                    env[name] = series[i] if i < len(series) else 0

            # 评估条件
            try:
                if position == 0:
                    # 检查开仓
                    if eval(long_condition, {"__builtins__": {}}, env):
                        position = 1
                        trades.append({
                            "direction": "long",
                            "entry_price": env['close'],
                            "entry_time": i
                        })
                    elif eval(short_condition, {"__builtins__": {}}, env):
                        position = -1
                        trades.append({
                            "direction": "short",
                            "entry_price": env['close'],
                            "entry_time": i
                        })
                else:
                    # 检查平仓
                    if position == 1 and eval(short_condition, {"__builtins__": {}}, env):
                        trades[-1]["exit_price"] = env['close']
                        trades[-1]["exit_time"] = i
                        position = 0
                    elif position == -1 and eval(long_condition, {"__builtins__": {}}, env):
                        trades[-1]["exit_price"] = env['close']
                        trades[-1]["exit_time"] = i
                        position = 0
            except Exception as e:
                logger.warning(f"条件评估失败：{e}")
                continue

        # 计算统计指标
        return self._calculate_metrics(trades)

    def _calculate_metrics(self, trades: list) -> dict:
        """计算回测指标"""
        if not trades:
            return {
                "success": True,
                "trades_count": 0,
                "sharpe_ratio": 0.0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "annual_return": 0.0
            }

        # 计算盈亏
        completed_trades = [t for t in trades if 'exit_price' in t]
        if not completed_trades:
            return {
                "success": True,
                "trades_count": 0,
                "sharpe_ratio": 0.0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "annual_return": 0.0
            }

        pnls = []
        wins = 0
        for trade in completed_trades:
            if trade['direction'] == 'long':
                pnl = trade['exit_price'] - trade['entry_price']
            else:
                pnl = trade['entry_price'] - trade['exit_price']

            pnls.append(pnl)
            if pnl > 0:
                wins += 1

        # 计算指标
        import numpy as np
        pnls_array = np.array(pnls)
        sharpe = np.mean(pnls_array) / np.std(pnls_array) if np.std(pnls_array) > 0 else 0
        win_rate = wins / len(completed_trades) if completed_trades else 0

        return {
            "success": True,
            "trades_count": len(completed_trades),
            "sharpe_ratio": float(sharpe),
            "win_rate": float(win_rate),
            "max_drawdown": 0.0,  # TODO: 计算最大回撤
            "annual_return": float(np.sum(pnls_array))
        }

    def _extract_results(self, api) -> dict:
        """提取回测结果"""
        # TODO: 从api中提取统计信息
        return {
            "success": True,
            "trades_count": 0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
            "annual_return": 0.0
        }


async def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='tqsdk标准回测')
    parser.add_argument('yaml_path', help='策略YAML文件路径')
    parser.add_argument('--start', default='2024-01-01', help='开始日期')
    parser.add_argument('--end', default='2026-04-08', help='结束日期')
    args = parser.parse_args()

    # 执行回测
    backtester = TqsdkBacktester()
    result = await backtester.backtest_strategy(
        args.yaml_path,
        args.start,
        args.end
    )

    # 输出结果
    print("\n" + "=" * 60)
    print("tqsdk回测结果")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
