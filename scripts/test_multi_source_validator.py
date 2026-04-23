#!/usr/bin/env python3
"""测试多源交叉验证器

验证：
1. 多数据源特征计算
2. 交叉验证逻辑
3. 一致性评分
4. 置信度调整
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.multi_source_validator import MultiSourceValidator


async def main():
    validator = MultiSourceValidator(
        mini_api_url="http://192.168.31.156:8105",
        tushare_token=None  # 暂不启用 Tushare
    )

    # 测试品种列表
    test_symbols = [
        "SHFE.rb2505",  # 螺纹钢
        "DCE.p2505",    # 棕榈油
        "SHFE.au2506",  # 黄金
    ]

    print("=" * 80)
    print("多源交叉验证器测试")
    print("=" * 80)

    for symbol in test_symbols:
        print(f"\n{'=' * 80}")
        print(f"品种: {symbol}")
        print("=" * 80)

        features, report = await validator.validate_features(
            symbol,
            enable_tushare=False  # 暂不启用 Tushare
        )

        if not features:
            print(f"❌ {symbol} 特征获取失败")
            continue

        # 输出特征
        print(f"\n【特征画像】")
        print(f"  波动率: {features.volatility_weighted} ({features.volatility_1y:.4f})")
        print(f"  趋势强度: {features.trend_strength_weighted} ({features.trend_strength_1y:.4f})")
        print(f"  流动性: {features.liquidity}")
        print(f"  置信度: {features.confidence.overall:.2f}")

        # 输出交叉验证报告
        print(f"\n【交叉验证报告】")
        print(f"  主数据源: {report.primary_source}")
        print(f"  验证数据源: {', '.join(report.validation_sources) if report.validation_sources else '无'}")
        print(f"  波动率一致性: {report.volatility_consistency:.2f}")
        print(f"  趋势一致性: {report.trend_consistency:.2f}")
        print(f"  总体一致性: {report.overall_consistency:.2f}")
        print(f"  验证结果: {'✅ 通过' if report.is_valid else '❌ 失败'}")
        print(f"  建议: {report.recommendation}")

        # 输出警告
        if report.warnings:
            print(f"\n【警告信息】")
            for warning in report.warnings:
                print(f"  ⚠️ {warning}")

        # 输出差异详情
        if report.volatility_diff:
            print(f"\n【差异详情】")
            for source, diff in report.volatility_diff.items():
                print(f"  波动率差异 ({source}): {diff:.4f}")
            for source, diff in report.trend_diff.items():
                print(f"  趋势差异 ({source}): {diff:.4f}")

    print(f"\n{'=' * 80}")
    print("测试完成")
    print("=" * 80)
    print("\n【说明】")
    print("当前仅使用 Mini API 单一数据源。")
    print("要启用多源交叉验证，需要：")
    print("1. 配置 Tushare Token")
    print("2. 实现 Tushare 数据获取逻辑")
    print("3. 设置 enable_tushare=True")


if __name__ == "__main__":
    asyncio.run(main())
