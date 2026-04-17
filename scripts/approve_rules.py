#!/usr/bin/env python3
"""批准新规则脚本 — TASK-U0-20260417-004

人工审核后，批准并部署新的参数映射规则。

使用方式:
python scripts/approve_rules.py <review_rules_path>

示例:
python scripts/approve_rules.py runtime/param_mapping_rules_review_20260417_020000.yaml
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.meta_optimizer import MetaOptimizer
from services.decision.src.llm.openai_client import OpenAICompatibleClient


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("❌ 用法: python scripts/approve_rules.py <review_rules_path>")
        sys.exit(1)

    review_path = sys.argv[1]

    print("="*60)
    print("📝 批准新规则")
    print("="*60)
    print(f"待审核规则: {review_path}")
    print()

    # 确认
    confirm = input("是否批准并部署新规则？(yes/no): ")
    if confirm.lower() not in ["yes", "y"]:
        print("❌ 已取消")
        sys.exit(0)

    # 初始化元优化器
    online_client = OpenAICompatibleClient()
    meta_optimizer = MetaOptimizer(
        online_client=online_client,
        rules_path="./runtime/param_mapping_rules.yaml",
        history_dir="./runtime/optimization_history"
    )

    # 批准规则
    success = meta_optimizer.approve_rules(review_path)

    if success:
        print("✅ 新规则已部署")
        print(f"旧规则已备份")
        print(f"当前规则: ./runtime/param_mapping_rules.yaml")
    else:
        print("❌ 规则部署失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
