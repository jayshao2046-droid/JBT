#!/usr/bin/env python3
"""Deterministic template-seed generation + baseline筛选 pipeline for TASK-0128."""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import logging
import re
import sys
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml


_BASE = Path(__file__).resolve().parent.parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))


DEFAULT_PRIMARY_TEMPLATE_ROOT = _BASE / "strategy_library"
DEFAULT_FALLBACK_TEMPLATE_ROOT = _BASE / "参考文件" / "因子策略库" / "入库标准化"
DEFAULT_GENERATED_DIR = _BASE / "strategies" / "template_seed_generated"
DEFAULT_REPORTS_DIR = _BASE / "strategies" / "template_seed_reports"
DEFAULT_CANDIDATES_DIR = _BASE / "strategies" / "template_seed_tuning_candidates"
DEFAULT_TIMEFRAMES = [5, 15, 30, 60, 120, 240]
DEFAULT_DATA_URL = "http://192.168.31.74:8105"

ALL_42_SYMBOLS = [
    "CZCE.AP", "CZCE.CF", "CZCE.FG", "CZCE.MA", "CZCE.OI",
    "CZCE.PF", "CZCE.RM", "CZCE.SA", "CZCE.SR", "CZCE.TA", "CZCE.UR",
    "DCE.a", "DCE.c", "DCE.cs", "DCE.eb", "DCE.eg",
    "DCE.i", "DCE.j", "DCE.jd", "DCE.jm", "DCE.l",
    "DCE.lh", "DCE.m", "DCE.p", "DCE.pg", "DCE.pp",
    "DCE.v", "DCE.y",
    "INE.sc",
    "SHFE.ag", "SHFE.al", "SHFE.au", "SHFE.bu", "SHFE.cu",
    "SHFE.fu", "SHFE.hc", "SHFE.ni", "SHFE.rb", "SHFE.ru",
    "SHFE.sp", "SHFE.ss", "SHFE.zn",
]

NIGHT_TRADING_PRODUCTS = {
    "rb", "hc", "cu", "al", "zn", "ni", "ss", "au", "ag",
    "fu", "bu", "ru", "sp", "sc",
    "i", "j", "jm", "p", "y", "m", "a", "c", "cs",
    "l", "v", "pp", "eg", "eb", "pg",
    "ma", "ta", "fg", "oi", "rm", "sa", "ur", "pf",
}

TIMEFRAME_RISK_SCALE = {
    5: 0.85,
    15: 0.95,
    30: 1.0,
    60: 1.0,
    120: 1.12,
    240: 1.25,
}

TIMEFRAME_CONFIRM_BARS = {
    5: 1,
    15: 1,
    30: 1,
    60: 1,
    120: 2,
    240: 2,
}

PRODUCT_TO_SYMBOL = {
    full_symbol.split(".", 1)[1].lower(): full_symbol
    for full_symbol in ALL_42_SYMBOLS
}


@dataclass(frozen=True)
class CandidateThresholds:
    min_sharpe: float = 0.5
    max_drawdown: float = 0.15
    min_win_rate: float = 0.45
    min_trades: int = 5


def normalize_symbol(symbol: str) -> str:
    raw = symbol.strip()
    if not raw:
        raise ValueError("symbol 不能为空")

    if "." not in raw:
        normalized = PRODUCT_TO_SYMBOL.get(raw.lower())
        if normalized is None:
            raise ValueError(f"未知品种: {raw}")
        return normalized

    exchange, product = raw.split(".", 1)
    for candidate in ALL_42_SYMBOLS:
        cand_exchange, cand_product = candidate.split(".", 1)
        if cand_exchange.lower() == exchange.lower() and cand_product.lower() == product.lower():
            return candidate

    exchange = exchange.upper()
    product = product.upper() if exchange == "CZCE" else product.lower()
    return f"{exchange}.{product}"


def split_symbol(symbol: str) -> tuple[str, str]:
    normalized = normalize_symbol(symbol)
    exchange, product = normalized.split(".", 1)
    return exchange, product


def resolve_data_url(explicit: str | None = None) -> str:
    if explicit:
        return explicit.rstrip("/")

    try:
        from src.core.settings import get_settings

        configured = get_settings().data_api_url.rstrip("/")
    except Exception:
        configured = ""

    if configured and configured not in {"http://localhost:8105", "http://127.0.0.1:8105"}:
        return configured
    return DEFAULT_DATA_URL


def resolve_template_roots(
    primary_root: Path | None = None,
    fallback_root: Path | None = None,
) -> list[Path]:
    roots: list[Path] = []
    for candidate in (
        primary_root or DEFAULT_PRIMARY_TEMPLATE_ROOT,
        fallback_root or DEFAULT_FALLBACK_TEMPLATE_ROOT,
    ):
        candidate = Path(candidate)
        if candidate.exists() and candidate not in roots:
            roots.append(candidate)
    if not roots:
        raise FileNotFoundError("未找到可用模板源目录")
    return roots


def _iter_yaml_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("*.yaml")
    yield from root.rglob("*.yml")


def _path_matches_symbol(path: Path, product: str) -> bool:
    product_lower = product.lower()
    normalized_parts = {part.strip().lower() for part in path.parts}
    if product_lower in normalized_parts:
        return True
    return re.search(rf"(^|[_\.]){re.escape(product_lower)}([_\.]|$)", path.stem.lower()) is not None


def discover_seed_templates(symbol: str, template_roots: Sequence[Path]) -> list[Path]:
    exchange, product = split_symbol(symbol)
    variants = {
        f"{exchange}.{product}",
        f"{exchange}.{product.lower()}",
        f"{exchange}.{product.upper()}",
        product,
        product.lower(),
        product.upper(),
    }
    matches: list[Path] = []
    seen: set[Path] = set()

    for root in template_roots:
        for variant in variants:
            candidate_dir = root / variant
            if not candidate_dir.exists() or not candidate_dir.is_dir():
                continue
            for yaml_path in sorted(_iter_yaml_files(candidate_dir)):
                resolved = yaml_path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    matches.append(yaml_path)

        if matches:
            continue

        for yaml_path in sorted(_iter_yaml_files(root)):
            if not _path_matches_symbol(yaml_path, product):
                continue
            resolved = yaml_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            matches.append(yaml_path)

    return matches


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"模板顶层必须是 mapping: {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)


def derive_base_timeframe(strategy: dict[str, Any], seed_path: Path) -> int:
    timeframe = strategy.get("timeframe_minutes")
    if isinstance(timeframe, int):
        return timeframe
    if isinstance(timeframe, str) and timeframe.isdigit():
        return int(timeframe)

    match = re.search(r"_(\d+)m(?:_|$)", str(strategy.get("name") or seed_path.stem), re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 60


def _replace_timeframe_token(text: str, base_timeframe: int, target_timeframe: int) -> str:
    updated = re.sub(
        rf"(?<!\d){base_timeframe}m(?!\d)",
        f"{target_timeframe}m",
        text,
        flags=re.IGNORECASE,
    )
    return re.sub(
        rf"(?<!\d){base_timeframe}\s*分钟(?!\d)",
        f"{target_timeframe}分钟",
        updated,
    )


def normalize_strategy_name(seed_name: str, exchange: str, product: str, target_timeframe: int) -> str:
    body = seed_name[6:] if seed_name.startswith("STRAT_") else seed_name
    body = re.sub(r"_(\d+)m(?=_|$)", f"_{target_timeframe}m", body)
    if not re.search(rf"_{target_timeframe}m(?=_|$)", body):
        body = f"{body}_{target_timeframe}m"

    lower_prefix = f"{exchange.lower()}_{product.lower()}_"
    lower_body = body.lower()
    if lower_body.startswith(lower_prefix):
        suffix = body[len(lower_prefix):]
    elif lower_body.startswith(f"{product.lower()}_"):
        suffix = body[len(product) + 1:]
    else:
        suffix = body
    return f"STRAT_{exchange.lower()}_{product.lower()}_{suffix}"


def _midpoint(value: Any) -> float | None:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (float(value[0]) + float(value[1])) / 2.0
    return None


def _timeframe_scale(target_timeframe: int, base_timeframe: int) -> float:
    if target_timeframe in TIMEFRAME_RISK_SCALE:
        return TIMEFRAME_RISK_SCALE[target_timeframe]
    if base_timeframe <= 0:
        return 1.0
    ratio = max(target_timeframe, 1) / max(base_timeframe, 1)
    return max(0.8, min(1.25, ratio ** 0.15))


def apply_param_seeds(
    strategy: dict[str, Any],
    search_space: dict[str, Any],
    target_timeframe: int,
    base_timeframe: int,
) -> None:
    signal = strategy.setdefault("signal", {})
    risk = strategy.setdefault("risk", {})
    stop_loss = risk.setdefault("stop_loss", {})
    take_profit = risk.setdefault("take_profit", {})

    stop_loss["type"] = "atr"
    take_profit["type"] = "atr"

    atr_midpoint = _midpoint(search_space.get("atr_multiplier"))
    base_atr = atr_midpoint
    if base_atr is None:
        base_atr = float(stop_loss.get("atr_multiplier") or 2.0)

    scaled_atr = round(base_atr * _timeframe_scale(target_timeframe, base_timeframe), 2)
    stop_loss["atr_multiplier"] = scaled_atr
    take_profit["atr_multiplier"] = round(max(scaled_atr * 1.2, scaled_atr + 0.25), 2)

    threshold = _midpoint(search_space.get("entry_threshold"))
    if threshold is not None:
        signal["long_threshold"] = round(threshold, 3)
        signal["short_threshold"] = round(-threshold, 3)

    adx_threshold = _midpoint(search_space.get("adx_threshold"))
    if adx_threshold is not None:
        adx_value = f"{adx_threshold:.2f}".rstrip("0").rstrip(".")
        for key in ("long_condition", "short_condition"):
            condition = signal.get(key)
            if isinstance(condition, str):
                signal[key] = re.sub(r"adx\s*>\s*\d+(?:\.\d+)?", f"adx > {adx_value}", condition)

    signal["confirm_bars"] = TIMEFRAME_CONFIRM_BARS.get(target_timeframe, signal.get("confirm_bars") or 1)


def build_strategy_yaml(
    seed_strategy: dict[str, Any],
    symbol: str,
    target_timeframe: int,
    source_path: Path,
    search_space: dict[str, Any] | None = None,
) -> dict[str, Any]:
    exchange, product = split_symbol(symbol)
    strategy = copy.deepcopy(seed_strategy)
    base_timeframe = derive_base_timeframe(seed_strategy, source_path)
    search_space = search_space or {}

    strategy_name = normalize_strategy_name(
        str(strategy.get("name") or source_path.stem),
        exchange,
        product,
        target_timeframe,
    )
    strategy["name"] = strategy_name
    strategy["timeframe_minutes"] = target_timeframe
    strategy["symbols"] = [f"KQ.m@{exchange}.{product}"]

    description = str(strategy.get("description") or strategy_name)
    strategy["description"] = _replace_timeframe_token(description, base_timeframe, target_timeframe)

    transaction_costs = strategy.setdefault("transaction_costs", {})
    transaction_costs.setdefault("slippage_per_unit", 1.0)
    transaction_costs.setdefault("commission_per_lot_round_turn", 3.0)

    risk = strategy.setdefault("risk", {})
    risk["force_close_day"] = "14:55"
    risk["no_overnight"] = True
    if product.lower() in NIGHT_TRADING_PRODUCTS:
        risk.setdefault("force_close_night", "22:55")

    apply_param_seeds(strategy, search_space, target_timeframe, base_timeframe)

    raw_tags = strategy.get("tags") or []
    tags: list[str] = []
    for tag in raw_tags:
        if isinstance(tag, str) and not re.fullmatch(r"\d+m", tag):
            tags.append(tag)
    tags.extend([exchange, product, f"{target_timeframe}m", "template_seed"])
    strategy["tags"] = list(dict.fromkeys(tags))

    strategy["template_seed"] = {
        "source": str(source_path),
        "base_timeframe_minutes": base_timeframe,
        "target_timeframe_minutes": target_timeframe,
        "symbol": normalize_symbol(symbol),
    }
    return strategy


def extract_baseline_metrics(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {}) if isinstance(report, dict) else {}
    status = summary.get("status") or report.get("status") or "failed"
    return {
        "status": status,
        "sharpe": float(summary.get("sharpe") or 0.0),
        "max_drawdown": float(summary.get("max_drawdown") or 1.0),
        "win_rate": float(summary.get("win_rate") or 0.0),
        "total_trades": int(summary.get("total_trades") or 0),
        "pnl": float(summary.get("pnl") or 0.0),
        "final_equity": float(summary.get("final_equity") or 0.0),
    }


def evaluate_candidate(
    baseline_report: dict[str, Any],
    tqsdk_valid: bool,
    tqsdk_errors: Sequence[str],
    thresholds: CandidateThresholds,
) -> dict[str, Any]:
    metrics = extract_baseline_metrics(baseline_report)
    reasons: list[str] = []

    if metrics["status"] != "completed":
        reasons.append(f"baseline status={metrics['status']}")
    if not tqsdk_valid:
        reasons.extend(tqsdk_errors)
    if metrics["sharpe"] < thresholds.min_sharpe:
        reasons.append(f"sharpe<{thresholds.min_sharpe}")
    if metrics["max_drawdown"] > thresholds.max_drawdown:
        reasons.append(f"max_drawdown>{thresholds.max_drawdown}")
    if metrics["win_rate"] < thresholds.min_win_rate:
        reasons.append(f"win_rate<{thresholds.min_win_rate}")
    if metrics["total_trades"] < thresholds.min_trades:
        reasons.append(f"total_trades<{thresholds.min_trades}")

    return {
        "is_candidate": not reasons,
        "reasons": reasons,
        "baseline": metrics,
        "tqsdk_valid": tqsdk_valid,
        "tqsdk_errors": list(tqsdk_errors),
    }


def serialize_for_json(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): serialize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize_for_json(item) for item in value]
    if isinstance(value, tuple):
        return [serialize_for_json(item) for item in value]
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(serialize_for_json(payload), handle, ensure_ascii=False, indent=2)


def default_date_range() -> tuple[str, str]:
    end_date = date.today()
    start_date = end_date - timedelta(days=180)
    return start_date.isoformat(), end_date.isoformat()


def build_parser() -> argparse.ArgumentParser:
    default_start_date, default_end_date = default_date_range()
    parser = argparse.ArgumentParser(description="运行 deterministic template-seed baseline pipeline")
    parser.add_argument("--symbols", nargs="*", help="品种列表，支持 rb / SHFE.rb / CZCE.CF")
    parser.add_argument("--timeframes", nargs="*", type=int, default=DEFAULT_TIMEFRAMES, help="目标周期列表")
    parser.add_argument("--template-root", type=Path, default=DEFAULT_PRIMARY_TEMPLATE_ROOT, help="主模板源目录")
    parser.add_argument("--fallback-template-root", type=Path, default=DEFAULT_FALLBACK_TEMPLATE_ROOT, help="回退模板源目录")
    parser.add_argument("--generated-dir", type=Path, default=DEFAULT_GENERATED_DIR, help="生成 YAML 输出目录")
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR, help="报告输出目录")
    parser.add_argument("--candidates-dir", type=Path, default=DEFAULT_CANDIDATES_DIR, help="候选 YAML 输出目录")
    parser.add_argument("--data-url", help="data API 地址")
    parser.add_argument("--start-date", default=default_start_date, help="baseline 开始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", default=default_end_date, help="baseline 结束日期 YYYY-MM-DD")
    parser.add_argument("--initial-capital", type=float, default=500000.0, help="baseline 初始资金")
    parser.add_argument("--max-templates-per-symbol", type=int, default=0, help="每个品种最多使用多少个 seed 模板，0 表示全部")
    parser.add_argument("--skip-baseline", action="store_true", help="仅生成 YAML，不执行 baseline")
    parser.add_argument("--min-sharpe", type=float, default=0.5, help="候选最小 Sharpe")
    parser.add_argument("--max-drawdown", type=float, default=0.15, help="候选最大回撤")
    parser.add_argument("--min-win-rate", type=float, default=0.45, help="候选最小胜率")
    parser.add_argument("--min-trades", type=int, default=5, help="候选最少成交笔数")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    return parser


def _report_relpath(path: Path) -> str:
    try:
        return str(path.relative_to(_BASE))
    except ValueError:
        return str(path)


@asynccontextmanager
async def optional_local_backtest_client(enabled: bool, data_url: str):
    if not enabled:
        yield None
        return

    from src.research.local_formal_backtest_client import LocalFormalBacktestClient

    async with LocalFormalBacktestClient(data_url=data_url) as client:
        yield client


async def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("template_seed_pipeline")

    symbols = [normalize_symbol(item) for item in (args.symbols or ALL_42_SYMBOLS)]
    timeframes = list(dict.fromkeys(int(value) for value in args.timeframes))
    template_roots = resolve_template_roots(args.template_root, args.fallback_template_root)
    data_url = resolve_data_url(args.data_url)
    thresholds = CandidateThresholds(
        min_sharpe=args.min_sharpe,
        max_drawdown=args.max_drawdown,
        min_win_rate=args.min_win_rate,
        min_trades=args.min_trades,
    )

    from src.research.param_mapping_applicator import ParamMappingApplicator
    from src.research.symbol_profiler import SymbolProfiler
    from src.research.tqsdk_backtest_client import TqSdkBacktestClient

    profiler = SymbolProfiler(data_service_url=data_url)
    applicator = ParamMappingApplicator()
    generated_count = 0
    candidate_count = 0
    missing_symbols: list[str] = []
    per_symbol: dict[str, dict[str, Any]] = {}

    async with TqSdkBacktestClient(data_url=data_url) as tqsdk_client:
        async with optional_local_backtest_client(not args.skip_baseline, data_url) as local_client:
            for symbol in symbols:
                logger.info("处理品种: %s", symbol)
                seed_templates = discover_seed_templates(symbol, template_roots)
                if args.max_templates_per_symbol > 0:
                    seed_templates = seed_templates[: args.max_templates_per_symbol]

                if not seed_templates:
                    missing_symbols.append(symbol)
                    per_symbol[symbol] = {"generated": 0, "candidates": 0, "missing_templates": True}
                    logger.warning("未找到模板: %s", symbol)
                    continue

                features = None
                search_space: dict[str, Any] = {}
                try:
                    features = await profiler.calculate_features(symbol=symbol)
                    if features is not None:
                        search_space = applicator.generate_search_space(features)
                except Exception as exc:
                    logger.warning("品种画像失败 %s: %s", symbol, exc)

                symbol_generated = 0
                symbol_candidates = 0

                for seed_path in seed_templates:
                    seed_strategy = read_yaml(seed_path)
                    for timeframe in timeframes:
                        generated_strategy = build_strategy_yaml(
                            seed_strategy=seed_strategy,
                            symbol=symbol,
                            target_timeframe=timeframe,
                            source_path=seed_path,
                            search_space=search_space,
                        )
                        yaml_path = Path(args.generated_dir) / symbol / f"{generated_strategy['name']}.yaml"
                        write_yaml(yaml_path, generated_strategy)
                        generated_count += 1
                        symbol_generated += 1

                        if args.skip_baseline:
                            baseline_report: dict[str, Any] = {"status": "skipped"}
                        else:
                            try:
                                baseline_report = await local_client.run_backtest(
                                    yaml_path=yaml_path,
                                    start_date=args.start_date,
                                    end_date=args.end_date,
                                    initial_capital=args.initial_capital,
                                )
                            except Exception as exc:
                                baseline_report = {"status": "failed", "error": str(exc)}

                        tqsdk_valid, tqsdk_errors = tqsdk_client.validate_yaml(generated_strategy)
                        evaluation = evaluate_candidate(
                            baseline_report=baseline_report,
                            tqsdk_valid=tqsdk_valid,
                            tqsdk_errors=tqsdk_errors,
                            thresholds=thresholds,
                        )

                        report_payload = {
                            "symbol": symbol,
                            "seed_template": _report_relpath(seed_path),
                            "generated_yaml": _report_relpath(yaml_path),
                            "features": serialize_for_json(features) if features is not None else None,
                            "search_space": search_space,
                            "baseline_report": baseline_report,
                            "evaluation": evaluation,
                        }
                        # 同时写两份：策略文件夹内（generated_dir/{symbol}/reports/）和汇总报告目录
                        report_path = Path(args.generated_dir) / symbol / "reports" / f"{generated_strategy['name']}.json"
                        write_json(report_path, report_payload)
                        report_path_summary = Path(args.reports_dir) / symbol / f"{generated_strategy['name']}.json"
                        write_json(report_path_summary, report_payload)

                        if evaluation["is_candidate"]:
                            candidate_path = Path(args.candidates_dir) / symbol / f"{generated_strategy['name']}.yaml"
                            write_yaml(candidate_path, generated_strategy)
                            candidate_count += 1
                            symbol_candidates += 1

                per_symbol[symbol] = {
                    "generated": symbol_generated,
                    "candidates": symbol_candidates,
                    "missing_templates": False,
                }

    summary = {
        "task": "TASK-0128",
        "mode": "skip_baseline" if args.skip_baseline else "baseline",
        "symbols": symbols,
        "symbol_count": len(symbols),
        "timeframes": timeframes,
        "template_roots": [_report_relpath(path) for path in template_roots],
        "generated_count": generated_count,
        "candidate_count": candidate_count,
        "missing_symbols": missing_symbols,
        "per_symbol": per_symbol,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "thresholds": asdict(thresholds),
    }
    write_json(Path(args.reports_dir) / "summary.json", summary)
    write_json(Path(args.candidates_dir) / "manifest.json", summary)
    logger.info("完成: generated=%s candidates=%s", generated_count, candidate_count)
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    asyncio.run(run_pipeline(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())