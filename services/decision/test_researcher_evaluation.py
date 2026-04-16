#!/usr/bin/env python3
"""测试研究员报告评估流程

测试流程：
1. 从 Alienware API 读取最新研究员报告
2. 使用 phi4 对报告进行评级
3. 发送飞书通知
"""
import asyncio
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from llm.pipeline import LLMPipeline


async def main():
    print("=" * 60)
    print("测试研究员报告评估流程")
    print("=" * 60)
    print()

    # 初始化 pipeline
    print("1. 初始化 LLMPipeline...")
    pipeline = LLMPipeline()
    print(f"   - Alienware API: {pipeline.researcher_loader.data_service_url}")
    print(f"   - phi4 模型: {pipeline.researcher_phi4_scorer.model}")
    print()

    # 评估最新报告
    print("2. 评估最新研究员报告...")
    result = await pipeline.evaluate_researcher_report()

    if "error" in result:
        print(f"   ❌ 评估失败: {result['error']}")
        return

    # 显示原始报告数据
    print()
    print("DEBUG: 原始报告数据结构:")
    import json
    report_data = result.get('report', {})
    print(json.dumps(report_data, indent=2, ensure_ascii=False)[:2000])
    print()

    # 显示结果
    print("   ✅ 评估成功")
    print()
    print("3. 评估结果:")
    print(f"   - 报告ID: {result.get('report', {}).get('report_id', 'unknown')}")
    print(f"   - 生成时间: {result.get('report', {}).get('generated_at', 'unknown')}")
    print(f"   - phi4 评分: {result.get('score', 0):.0f} / 100")
    print(f"   - 置信度: {result.get('confidence', 'unknown')}")
    print(f"   - 飞书通知: {'✅ 已发送' if result.get('notification_sent') else '❌ 未发送'}")
    print()

    print("4. 评级理由:")
    reasoning = result.get('reasoning', '')
    if reasoning:
        print(f"   {reasoning}")
    print()

    print("5. 改进建议:")
    improvements = result.get('improvements', [])
    if improvements:
        for i, item in enumerate(improvements, 1):
            print(f"   {i}. {item}")
    else:
        print("   (无)")
    print()

    print(f"总耗时: {result.get('duration_seconds', 0):.2f} 秒")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
