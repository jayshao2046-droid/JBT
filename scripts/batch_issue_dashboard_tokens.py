#!/usr/bin/env python3
"""批量签发 TASK-DASHBOARD-001 全部 5 个批次 Token"""
import subprocess
import sys

LOCKCTL = "governance/jbt_lockctl.py"
TTL = "4320"

BATCHES = [
    {
        "task": "TASK-DASHBOARD-001-B2",
        "review": "REVIEW-DASHBOARD-001-B2",
        "notes": "回测模块完善: 策略审查+参数优化器+回测详情增强",
        "files": [
            "services/dashboard/dashboard_web/app/(dashboard)/backtest/review/page.tsx",
            "services/dashboard/dashboard_web/app/(dashboard)/backtest/optimizer/page.tsx",
            "services/dashboard/dashboard_web/app/(dashboard)/backtest/results/page.tsx",
            "services/dashboard/dashboard_web/lib/api/backtest.ts",
            "services/dashboard/dashboard_web/hooks/use-backtest.ts",
            "services/dashboard/dashboard_web/hooks/use-backtest-results.ts",
            "services/dashboard/dashboard_web/components/backtest/parameter-optimizer.tsx",
            "services/dashboard/dashboard_web/components/backtest/review-panel.tsx",
            "services/dashboard/dashboard_web/components/backtest/result-detail-dialog.tsx",
            "services/dashboard/dashboard_web/components/backtest/param-grid.tsx",
        ],
    },
    {
        "task": "TASK-DASHBOARD-001-B3",
        "review": "REVIEW-DASHBOARD-001-B3",
        "notes": "决策模块验证与补缺: 逐组件核实API连接+补缺",
        "files": [
            "services/dashboard/dashboard_web/app/(dashboard)/decision/page.tsx",
            "services/dashboard/dashboard_web/app/(dashboard)/decision/models/page.tsx",
            "services/dashboard/dashboard_web/app/(dashboard)/decision/research/page.tsx",
            "services/dashboard/dashboard_web/app/(dashboard)/decision/repository/page.tsx",
            "services/dashboard/dashboard_web/lib/api/decision.ts",
            "services/dashboard/dashboard_web/hooks/use-decision.ts",
            "services/dashboard/dashboard_web/components/decision/overview.tsx",
            "services/dashboard/dashboard_web/components/decision/models-factors.tsx",
            "services/dashboard/dashboard_web/components/decision/factor-analysis.tsx",
            "services/dashboard/dashboard_web/components/decision/research-center.tsx",
            "services/dashboard/dashboard_web/components/decision/evening-rotation-plan.tsx",
            "services/dashboard/dashboard_web/components/decision/post-market-report.tsx",
            "services/dashboard/dashboard_web/components/decision/strategy-repository.tsx",
            "services/dashboard/dashboard_web/components/decision/strategy-import.tsx",
            "services/dashboard/dashboard_web/components/decision/stock-pool-table.tsx",
        ],
    },
    {
        "task": "TASK-DASHBOARD-001-B4",
        "review": "REVIEW-DASHBOARD-001-B4",
        "notes": "数据模块增强: 数据探索器+新闻流+系统监控增强",
        "files": [
            "services/dashboard/dashboard_web/app/(dashboard)/data/explorer/page.tsx",
            "services/dashboard/dashboard_web/app/(dashboard)/data/news/page.tsx",
            "services/dashboard/dashboard_web/app/(dashboard)/data/system/page.tsx",
            "services/dashboard/dashboard_web/lib/api/data.ts",
            "services/dashboard/dashboard_web/components/data/data-explorer.tsx",
            "services/dashboard/dashboard_web/components/data/news-feed.tsx",
            "services/dashboard/dashboard_web/components/data/system-monitor.tsx",
        ],
    },
    {
        "task": "TASK-DASHBOARD-001-B5",
        "review": "REVIEW-DASHBOARD-001-B5",
        "notes": "系统设置后端对接: settings API客户端+设置页面连接",
        "files": [
            "services/dashboard/dashboard_web/app/(dashboard)/settings/page.tsx",
            "services/dashboard/dashboard_web/app/(dashboard)/settings/layout.tsx",
            "services/dashboard/dashboard_web/lib/api/settings.ts",
        ],
    },
]


def main():
    for batch in BATCHES:
        cmd = [
            sys.executable, LOCKCTL, "issue",
            "--task", batch["task"],
            "--agent", "Livis",
            "--action", "edit",
            "--ttl-minutes", TTL,
            "--review-id", batch["review"],
            "--notes", batch["notes"],
            "--files",
        ] + batch["files"]

        print(f"\n{'='*60}")
        print(f"签发: {batch['task']}")
        print(f"文件数: {len(batch['files'])}")
        print(f"{'='*60}")

        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            print(f"ERROR: {batch['task']} 签发失败")
            sys.exit(1)

    print(f"\n{'='*60}")
    print("全部 4 个 Token 签发完成 (B2-B5)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
