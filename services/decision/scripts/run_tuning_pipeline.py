#!/usr/bin/env python3
"""策略调优串行流水线 — TASK-0122-B

功能：
1. 检查 Mini data API 和 Studio Ollama 连通性（不可用时直接退出，不降级）
2. 按 trend → oscillation → reversal 顺序串行处理每个 YAML 策略
3. 每个策略：基线回测 → Optuna IS/OOS 优化 → 飞书通知 → 报告输出
4. 全部完成后输出汇总报告

用法：
    cd /Users/jayshao/JBT/services/decision
    source ../../.venv/bin/activate
    python scripts/run_tuning_pipeline.py \\
        --symbol p \\
        --data-url http://192.168.31.76:8105 \\
        --ollama-url http://192.168.31.142:11434 \\
        --start 2021-01-01 \\
        --end 2026-01-01 \\
        --n-trials 100 \\
        --feishu-webhook https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml

# 把 services/decision 的 src 加入路径
_BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE))

from src.research.yaml_signal_executor import YAMLSignalExecutor
from src.research.strategy_param_optimizer import StrategyParamOptimizer
from src.research.strategy_evaluator import StrategyEvaluator

# 硬性约束：策略 YAML 必须满足，否则跳过优化直接标记 BLOCKED
_HARD_CONSTRAINTS = [
    ("risk.force_close_day", lambda r: r.get("force_close_day", "") == "14:55",
     "force_close_day 必须为 14:55"),
    ("risk.daily_loss_limit_yuan", lambda r: r.get("daily_loss_limit_yuan", 99999) <= 2000,
     "daily_loss_limit_yuan 必须 ≤ 2000 元"),
    ("risk.per_symbol_fuse_yuan", lambda r: r.get("per_symbol_fuse_yuan", 99999) <= 1000,
     "per_symbol_fuse_yuan（单笔止损）必须 ≤ 1000 元"),
    ("risk.no_overnight", lambda r: bool(r.get("no_overnight", False)),
     "no_overnight 必须为 true，禁止隔夜"),
]


def _check_hard_constraints(strategy: dict) -> list[str]:
    """返回所有不满足的硬性约束描述列表。空列表表示全部通过。"""
    risk = strategy.get("risk", {})
    violations = []
    for _key, check_fn, msg in _HARD_CONSTRAINTS:
        if not check_fn(risk):
            violations.append(msg)
    return violations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tuning_pipeline")

STRATEGY_ROOT = _BASE / "参考文件" / "因子策略库" / "入库标准化"
REPORTS_DIR = _BASE / "reports" / "tuning"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

STYLE_ORDER = ["trend", "oscillation", "reversal", "breakout", "mixed", "arbitrage"]


# ──────────────────────────────────────────────────────────────
# 前置连通性检查
# ──────────────────────────────────────────────────────────────

async def check_services(data_url: str, ollama_url: str) -> None:
    """检查 Mini data API 和 Studio Ollama，任一不可用则退出。"""
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=8.0) as client:
        # Mini data API
        try:
            resp = await client.get(f"{data_url}/api/v1/symbols")
            resp.raise_for_status()
            logger.info("✅ Mini data API 在线: %s", data_url)
        except Exception as e:
            errors.append(f"Mini data API 不可达 ({data_url}): {e}")

        # Studio Ollama
        try:
            resp = await client.get(f"{ollama_url}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            for required in ["deepcoder:14b", "phi4-reasoning:14b"]:
                if required not in models:
                    errors.append(f"Studio Ollama 缺少模型: {required}（已加载: {models}）")
                else:
                    logger.info("✅ 模型就绪: %s", required)
        except Exception as e:
            errors.append(f"Studio Ollama 不可达 ({ollama_url}): {e}")

    if errors:
        for err in errors:
            logger.error("❌ %s", err)
        logger.error("前置检查失败，流水线退出（不降级）。请修复上述问题后重试。")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────
# 飞书通知
# ──────────────────────────────────────────────────────────────

async def send_feishu(webhook_url: str, strategy_id: str, result: dict[str, Any]) -> None:
    """发送策略完成飞书卡片通知（标准 turquoise 通知格式）。"""
    if not webhook_url:
        return

    baseline = result.get("baseline", {})
    optimized = result.get("optimized", {})
    oos_verdict = result.get("oos_verdict", {})
    passed_oos = result.get("passed_oos", False)

    grade_icon = "🟢" if passed_oos else "🔴"
    status_label = "✅ OOS 通过" if passed_oos else "❌ OOS 未通过"

    def fmt(v: Any, pct: bool = False) -> str:
        if v is None:
            return "N/A"
        if pct:
            return f"{float(v) * 100:.2f}%"
        return f"{float(v):.4f}"

    body = (
        f"**策略 ID**：`{strategy_id}`\n"
        f"**状态**：{status_label}\n\n"
        f"**基线指标**\n"
        f"- Sharpe: {fmt(baseline.get('sharpe_ratio'))}"
        f" | 最大回撤: {fmt(baseline.get('max_drawdown'), pct=True)}"
        f" | 胜率: {fmt(baseline.get('win_rate'), pct=True)}"
        f" | 年化: {fmt(baseline.get('annualized_return'), pct=True)}\n\n"
        f"**优化后 IS 指标**\n"
        f"- Sharpe: {fmt(optimized.get('is_sharpe'))}"
        f" | OOS Sharpe: {fmt(oos_verdict.get('oos_sharpe'))}"
        f" | IS/OOS 比: {fmt(oos_verdict.get('is_oos_ratio'))}\n\n"
        f"**OOS 验收**：{'全部通过' if passed_oos else '、'.join(oos_verdict.get('fail_reasons', ['未知']))}"
    )

    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📊 [RESEARCH-TUNING] {strategy_id} 调优完成"},
                "template": "turquoise",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": body},
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": f"JBT decision | {ts}"}],
                },
            ],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code == 200:
                logger.info("📣 飞书通知已发送: %s", strategy_id)
            else:
                logger.warning("飞书通知失败 %s: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("飞书通知异常 (%s): %s", strategy_id, e)


# ──────────────────────────────────────────────────────────────
# 单策略处理
# ──────────────────────────────────────────────────────────────

async def process_one_strategy(
    yaml_path: Path,
    executor: YAMLSignalExecutor,
    optimizer: StrategyParamOptimizer,
    evaluator: StrategyEvaluator,
    start_date: str,
    end_date: str,
    feishu_webhook: str,
    idx: int,
    total: int,
    *,
    iterative: bool = False,
) -> dict[str, Any]:
    """处理单个策略：硬性约束预检 + 基线 + 优化 + 评级 + 报告 + 通知。"""
    strategy_id = yaml_path.stem
    logger.info("\n═══ [%d/%d] 开始处理: %s ═══", idx, total, strategy_id)

    with open(yaml_path, "r", encoding="utf-8") as f:
        strategy = yaml.safe_load(f)

    result: dict[str, Any] = {
        "strategy_id": strategy_id,
        "yaml_path": str(yaml_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # ── 0. 硬性约束预检 ──
    violations = _check_hard_constraints(strategy)
    if violations:
        logger.warning("  ⛔ 硬性约束不满足，跳过优化: %s", violations)
        result["error"] = "硬性约束违规: " + " | ".join(violations)
        result["hard_constraint_violations"] = violations
        result["passed_oos"] = False
        result["oos_verdict"] = {}
        result["grade"] = "BLOCKED"
        _save_report(strategy_id, result)
        await send_feishu(feishu_webhook, strategy_id, result)
        return result

    # ── 1. 基线回测（全量数据）──
    if iterative and hasattr(executor, 'execute_with_iterative_optimization'):
        logger.info("  [1/2] 迭代优化回测 %s ...", strategy_id)
        baseline_result, iteration_history = await executor.execute_with_iterative_optimization(
            strategy, start_date, end_date
        )
        result["baseline"] = baseline_result.to_dict()
        result["iteration_history"] = iteration_history
    else:
        logger.info("  [1/2] 基线回测 %s ...", strategy_id)
        baseline_result = await executor.execute(strategy, start_date, end_date)
        result["baseline"] = baseline_result.to_dict()

    if baseline_result.status == "failed":
        logger.error("  基线回测失败: %s", baseline_result.error)
        result["error"] = baseline_result.error
        result["passed_oos"] = False
        result["oos_verdict"] = {}
        _save_report(strategy_id, result)
        await send_feishu(feishu_webhook, strategy_id, result)
        return result

    logger.info(
        "  基线结果 — Sharpe: %.4f | 回撤: %.2f%% | 胜率: %.2f%% | 年化: %.2f%%",
        baseline_result.sharpe_ratio,
        baseline_result.max_drawdown * 100,
        baseline_result.win_rate * 100,
        baseline_result.annualized_return * 100,
    )

    # ── 2. Optuna IS/OOS 优化 ──
    logger.info("  [2/2] Optuna 优化 %s (%d trials)...", strategy_id, optimizer.n_trials)
    opt_result = await optimizer.optimize(strategy, start_date, end_date)

    if "error" in opt_result:
        logger.error("  优化失败: %s", opt_result["error"])
        result["error"] = opt_result["error"]
        result["passed_oos"] = False
        result["oos_verdict"] = {}
        result["optimized"] = {}
    else:
        result["best_params"] = opt_result.get("best_params", {})
        result["optimized"] = {
            "is_sharpe": opt_result.get("oos_verdict", {}).get("is_sharpe"),
            "oos_sharpe": opt_result.get("oos_verdict", {}).get("oos_sharpe"),
            "is_result": opt_result.get("is_result", {}),
            "oos_result": opt_result.get("oos_result", {}),
        }
        result["passed_oos"] = opt_result.get("passed_oos", False)
        result["oos_verdict"] = opt_result.get("oos_verdict", {})
        result["is_end"] = opt_result.get("is_end")
        result["oos_start"] = opt_result.get("oos_start")

        logger.info(
            "  优化结果 — IS Sharpe: %.4f | OOS Sharpe: %.4f | OOS 通过: %s",
            result["oos_verdict"].get("is_sharpe", 0),
            result["oos_verdict"].get("oos_sharpe", 0),
            "✅" if result["passed_oos"] else "❌",
        )
        if not result["passed_oos"]:
            for reason in result["oos_verdict"].get("fail_reasons", []):
                logger.warning("    OOS 未通过原因: %s", reason)

    # ── 3. StrategyEvaluator 完整评级 ──
    try:
        eval_report = await evaluator.evaluate_strategy(str(yaml_path), start_date, end_date)
        result["eval_score"] = eval_report.get("final_score", 0)
        result["eval_grade"] = eval_report.get("grade", "?")
        result["eval_breakdown"] = eval_report.get("breakdown", {})
        result["eval_conclusion"] = eval_report.get("conclusion", {})
        logger.info(
            "  📊 评估结果 — 得分: %d/100 | 等级: %s | 可上线: %s",
            result["eval_score"],
            result["eval_grade"],
            "✅" if eval_report.get("conclusion", {}).get("can_deploy") else "❌",
        )
    except Exception as e:
        logger.warning("  评估器异常（不影响主流程）: %s", e)
        result["eval_score"] = None
        result["eval_grade"] = "?"

    # ── 4. 保存报告 ──
    _save_report(strategy_id, result)

    # ── 5. 飞书通知 ──
    await send_feishu(feishu_webhook, strategy_id, result)

    return result


def _save_report(strategy_id: str, result: dict[str, Any]) -> None:
    """保存 JSON 报告到 reports/tuning/。"""
    report_path = REPORTS_DIR / f"{strategy_id}_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info("  📄 报告已保存: %s", report_path)


# ──────────────────────────────────────────────────────────────
# 汇总报告
# ──────────────────────────────────────────────────────────────

def print_summary(results: list[dict[str, Any]]) -> None:
    """打印所有策略汇总表格。"""
    logger.info("\n\n╔══════════════════════════════════════════════════════════════╗")
    logger.info("║                     调优流水线汇总报告                        ║")
    logger.info("╚══════════════════════════════════════════════════════════════╝")
    logger.info("%-38s %-10s %-10s %-10s %-8s %-8s %-6s",
                "策略 ID", "基线Sharpe", "IS Sharpe", "OOS Sharpe", "OOS通过", "评分", "等级")
    logger.info("-" * 92)

    passed = 0
    failed = 0
    blocked = 0
    for r in results:
        sid = r.get("strategy_id", "?")
        baseline_s = r.get("baseline", {}).get("sharpe_ratio", 0) or 0
        is_s = r.get("oos_verdict", {}).get("is_sharpe", 0) or 0
        oos_s = r.get("oos_verdict", {}).get("oos_sharpe", 0) or 0
        ok = r.get("passed_oos", False)
        grade = r.get("eval_grade", r.get("grade", "?"))
        score = r.get("eval_score", "-")
        if grade == "BLOCKED":
            blocked += 1
        elif ok:
            passed += 1
        else:
            failed += 1
        logger.info(
            "%-38s %-10.4f %-10.4f %-10.4f %-8s %-8s %-6s",
            sid[:38], baseline_s, is_s, oos_s,
            "✅" if ok else ("⛔" if grade == "BLOCKED" else "❌"),
            str(score), grade,
        )

    logger.info("-" * 92)
    logger.info("总计 %d 个策略：%d 通过 OOS ✅ | %d 未通过 ❌ | %d 硬约束阻断 ⛔",
                len(results), passed, failed, blocked)
    logger.info("通过率：%.1f%%", passed / len(results) * 100 if results else 0)

    # 保存汇总 JSON
    summary_path = REPORTS_DIR / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "passed": passed, "failed": failed}, f, ensure_ascii=False, indent=2)
    logger.info("汇总报告: %s", summary_path)


# ──────────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────────

async def main() -> None:
    parser = argparse.ArgumentParser(description="策略调优串行流水线 TASK-0122-B")
    parser.add_argument("--symbol", required=True, help="品种代码，如 p（棕榈油）")
    parser.add_argument("--data-url", default="http://192.168.31.76:8105", help="Mini data API URL")
    parser.add_argument("--ollama-url", default="http://192.168.31.142:11434", help="Studio Ollama URL")
    parser.add_argument("--start", default="2021-01-01", help="回测起始日期 YYYY-MM-DD")
    parser.add_argument("--end", default="2026-01-01", help="回测结束日期 YYYY-MM-DD")
    parser.add_argument("--n-trials", type=int, default=100, help="Optuna trial 数量")
    parser.add_argument(
        "--feishu-webhook",
        default=os.getenv("FEISHU_WEBHOOK_URL", ""),
        help="飞书 Webhook URL（或设置 FEISHU_WEBHOOK_URL 环境变量）",
    )
    parser.add_argument("--sector", default=None, help="限定 sector 目录（如 oilseed）")
    parser.add_argument("--iterative", action="store_true", default=False,
                        help="启用迭代优化（ThreeTierOptimizer）替代普通基线回测")
    args = parser.parse_args()

    logger.info("╔══════════════════════════════════════════════════════════════╗")
    logger.info("║              JBT 策略调优流水线 TASK-0122-B                  ║")
    logger.info("╚══════════════════════════════════════════════════════════════╝")
    logger.info("品种: %s | 回测区间: %s ~ %s | trials: %d", args.symbol, args.start, args.end, args.n_trials)

    # 前置检查
    await check_services(args.data_url, args.ollama_url)

    # 收集 YAML 文件（按 sector/symbol/style 排序）
    yaml_files: list[Path] = []
    search_root = STRATEGY_ROOT
    if args.sector:
        search_root = STRATEGY_ROOT / args.sector / args.symbol
    else:
        # 自动搜索所有 sector
        for sector_dir in sorted(STRATEGY_ROOT.iterdir()):
            if not sector_dir.is_dir():
                continue
            sym_dir = sector_dir / args.symbol
            if not sym_dir.is_dir():
                continue
            search_root = sym_dir
            break

    if not search_root.is_dir():
        logger.error("未找到品种目录: %s（搜索路径: %s）", args.symbol, STRATEGY_ROOT)
        sys.exit(1)

    # 按 STYLE_ORDER 排序
    for style in STYLE_ORDER:
        style_dir = search_root / style
        if style_dir.is_dir():
            yaml_files.extend(sorted(style_dir.glob("*.yaml")))

    # 也收集不在子目录里的 yaml
    yaml_files.extend(sorted(p for p in search_root.glob("*.yaml") if p not in yaml_files))

    if not yaml_files:
        logger.error("品种 %s 下未找到任何 YAML 策略文件（路径: %s）", args.symbol, search_root)
        sys.exit(1)

    logger.info("找到 %d 个策略文件，开始串行处理...\n", len(yaml_files))
    for i, f in enumerate(yaml_files, 1):
        logger.info("  [%02d] %s", i, f.name)

    # 初始化执行器、优化器和评估器
    executor = YAMLSignalExecutor(
        data_service_url=args.data_url,
        ollama_url=args.ollama_url,
    )
    optimizer = StrategyParamOptimizer(executor=executor, n_trials=args.n_trials)
    evaluator = StrategyEvaluator(
        data_service_url=args.data_url,
        ollama_url=args.ollama_url,
    )

    # 串行处理
    all_results: list[dict[str, Any]] = []
    for idx, yaml_path in enumerate(yaml_files, 1):
        try:
            result = await process_one_strategy(
                yaml_path=yaml_path,
                executor=executor,
                optimizer=optimizer,
                evaluator=evaluator,
                start_date=args.start,
                end_date=args.end,
                feishu_webhook=args.feishu_webhook,
                idx=idx,
                total=len(yaml_files),
                iterative=args.iterative,
            )
            all_results.append(result)
        except Exception as e:
            logger.exception("策略 %s 处理异常: %s", yaml_path.stem, e)
            all_results.append({"strategy_id": yaml_path.stem, "error": str(e), "passed_oos": False})

    # 汇总
    print_summary(all_results)
    logger.info("\n🎉 全部 %d 个策略处理完成，等待用户确认后继续下一品种。", len(yaml_files))


if __name__ == "__main__":
    asyncio.run(main())
