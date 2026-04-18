"""策略池管理器 - 熔断机制

当策略触发熔断时，从预生成的9个策略池中调取新策略继续测试。

策略池：
- 橡胶（ru）：3个策略
- 螺纹钢（rb）：3个策略
- 棕榈油（p）：3个策略
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "services" / "decision" / ".env")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StrategyPool:
    """策略池管理器"""

    def __init__(self, strategies_dir: str = "strategies"):
        self.strategies_dir = Path(strategies_dir)
        self.available_strategies = self._load_strategy_pool()
        self.used_strategies = set()

    def _load_strategy_pool(self) -> List[str]:
        """加载策略池"""
        if not self.strategies_dir.exists():
            logger.warning(f"策略目录不存在：{self.strategies_dir}")
            return []

        # 查找所有YAML文件
        strategies = list(self.strategies_dir.glob("*.yaml"))
        logger.info(f"📦 策略池加载完成：{len(strategies)} 个策略")

        # 按品种分组
        by_symbol = {}
        for s in strategies:
            # 从文件名提取品种（如 rb_xxx.yaml -> rb）
            symbol = s.stem.split('_')[0]
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(str(s))

        for symbol, strats in by_symbol.items():
            logger.info(f"  - {symbol}: {len(strats)} 个策略")

        return [str(s) for s in strategies]

    def get_next_strategy(self, symbol_prefix: Optional[str] = None) -> Optional[str]:
        """获取下一个未使用的策略

        Args:
            symbol_prefix: 品种前缀（如 'rb'），如果指定则只返回该品种的策略

        Returns:
            策略YAML路径，如果没有可用策略则返回None
        """
        available = [
            s for s in self.available_strategies
            if s not in self.used_strategies
        ]

        # 按品种过滤
        if symbol_prefix:
            available = [
                s for s in available
                if Path(s).stem.startswith(symbol_prefix)
            ]

        if not available:
            logger.warning(f"⚠️ 没有可用的策略（品种：{symbol_prefix or '全部'}）")
            return None

        # 返回第一个可用策略
        next_strategy = available[0]
        self.used_strategies.add(next_strategy)
        logger.info(f"✅ 调取策略：{Path(next_strategy).name}")
        logger.info(f"📊 剩余策略：{len(available) - 1} 个")

        return next_strategy

    def mark_as_used(self, strategy_path: str):
        """标记策略为已使用"""
        self.used_strategies.add(strategy_path)

    def reset(self):
        """重置策略池（清除已使用标记）"""
        self.used_strategies.clear()
        logger.info("🔄 策略池已重置")

    def get_stats(self) -> dict:
        """获取策略池统计信息"""
        total = len(self.available_strategies)
        used = len(self.used_strategies)
        available = total - used

        # 按品种统计
        by_symbol = {}
        for s in self.available_strategies:
            symbol = Path(s).stem.split('_')[0]
            if symbol not in by_symbol:
                by_symbol[symbol] = {"total": 0, "used": 0, "available": 0}

            by_symbol[symbol]["total"] += 1
            if s in self.used_strategies:
                by_symbol[symbol]["used"] += 1
            else:
                by_symbol[symbol]["available"] += 1

        return {
            "total": total,
            "used": used,
            "available": available,
            "by_symbol": by_symbol
        }


class CircuitBreakerManager:
    """熔断管理器"""

    def __init__(self, strategy_pool: StrategyPool):
        self.pool = strategy_pool
        self.circuit_breaker_count = 0
        self.max_circuit_breakers = 3  # 最多触发3次熔断

    def should_trigger_circuit_breaker(
        self,
        zero_score_count: int,
        small_improvement_count: int,
        r1_used: bool
    ) -> bool:
        """判断是否应触发熔断

        触发条件：
        1. 连续3次得分为0
        2. 连续5次改进<5%
        3. R1调用后仍无改进
        """
        if zero_score_count >= 3:
            logger.warning("⚠️ 熔断条件1：连续3次得分为0")
            return True

        if small_improvement_count >= 5:
            logger.warning("⚠️ 熔断条件2：连续5次改进<5%")
            return True

        if r1_used:
            logger.warning("⚠️ 熔断条件3：R1调用后仍无改进")
            return True

        return False

    def handle_circuit_breaker(self, current_symbol: str) -> Optional[str]:
        """处理熔断，返回新策略路径"""
        self.circuit_breaker_count += 1

        logger.warning("=" * 60)
        logger.warning(f"🔥 触发熔断 (第 {self.circuit_breaker_count} 次)")
        logger.warning("=" * 60)

        # 检查是否超过最大熔断次数
        if self.circuit_breaker_count > self.max_circuit_breakers:
            logger.error("❌ 超过最大熔断次数，停止测试")
            return None

        # 从策略池中调取新策略
        # 提取品种前缀（如 SHFE.rb2505 -> rb）
        symbol_prefix = None
        if '.' in current_symbol:
            contract = current_symbol.split('.')[1]
            # 提取字母部分
            symbol_prefix = ''.join([c for c in contract if not c.isdigit()])

        new_strategy = self.pool.get_next_strategy(symbol_prefix)

        if not new_strategy:
            logger.error("❌ 策略池已耗尽，无法继续测试")
            return None

        logger.info(f"✅ 切换到新策略：{Path(new_strategy).name}")
        return new_strategy


async def test_circuit_breaker():
    """测试熔断机制"""
    logger.info("=" * 60)
    logger.info("测试熔断机制")
    logger.info("=" * 60)

    # 初始化策略池
    pool = StrategyPool()
    stats = pool.get_stats()

    logger.info(f"\n策略池统计：")
    logger.info(f"  总计：{stats['total']} 个")
    logger.info(f"  可用：{stats['available']} 个")
    logger.info(f"  已用：{stats['used']} 个")
    logger.info(f"\n按品种分布：")
    for symbol, data in stats['by_symbol'].items():
        logger.info(f"  {symbol}: {data['available']}/{data['total']} 可用")

    # 初始化熔断管理器
    breaker = CircuitBreakerManager(pool)

    # 模拟熔断场景
    logger.info("\n" + "=" * 60)
    logger.info("模拟场景：螺纹钢策略连续失败")
    logger.info("=" * 60)

    current_symbol = "SHFE.rb2505"

    for i in range(5):
        logger.info(f"\n--- 第 {i + 1} 轮测试 ---")

        # 模拟触发熔断
        if breaker.should_trigger_circuit_breaker(
            zero_score_count=3,
            small_improvement_count=0,
            r1_used=False
        ):
            new_strategy = breaker.handle_circuit_breaker(current_symbol)

            if not new_strategy:
                logger.error("测试终止：无可用策略")
                break

            logger.info(f"继续测试新策略：{new_strategy}")
        else:
            logger.info("未触发熔断，继续当前策略")

    # 最终统计
    final_stats = pool.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("最终统计")
    logger.info("=" * 60)
    logger.info(f"熔断次数：{breaker.circuit_breaker_count}")
    logger.info(f"剩余策略：{final_stats['available']} 个")
    logger.info(f"已用策略：{final_stats['used']} 个")


if __name__ == "__main__":
    asyncio.run(test_circuit_breaker())
