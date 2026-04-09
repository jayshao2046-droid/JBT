from __future__ import annotations

from pathlib import Path
import re
import time
from datetime import datetime
from typing import Any, Dict, Mapping, Optional

import yaml

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import PlainTextResponse

if __package__:
    try:
        from ...backtest.strategy_base import StrategyConfigError
        from ...backtest.strategy_base import StrategyDefinition
        from ...backtest.strategy_base import strategy_registry
        from ...backtest.factor_registry import factor_registry as _factor_registry
    except ImportError:
        StrategyConfigError = ValueError
        StrategyDefinition = None
        strategy_registry = None
        _factor_registry = None
    from ...core.settings import get_settings
else:
    try:
        from backtest.strategy_base import StrategyConfigError
        from backtest.strategy_base import StrategyDefinition
        from backtest.strategy_base import strategy_registry
        from backtest.factor_registry import factor_registry as _factor_registry
    except ImportError:
        StrategyConfigError = ValueError
        StrategyDefinition = None
        strategy_registry = None
        _factor_registry = None
    from core.settings import get_settings

router = APIRouter(prefix="/api", tags=["support"])

ACTIVE_STATUSES = {"submitted", "running", "pending"}
COMPAT_STATE_ATTR = "backtest_compat_state"
METRIC_HISTORY_LIMIT = 24
EVENT_LOG_LIMIT = 20
SYSTEM_LOG_LIMIT = 80
MARKET_CACHE_TTL_SECONDS = 30

MAIN_CONTRACT_CATEGORIES: list[dict[str, Any]] = [
    {"key": "ferrous", "zh": "黑色系", "en": "Ferrous", "codes": ["rb", "hc", "i", "j", "jm", "sf", "sm"]},
    {"key": "non_ferrous", "zh": "有色金属", "en": "Non-Ferrous", "codes": ["cu", "al", "zn", "pb", "ni", "sn", "ss", "ao", "bc"]},
    {"key": "precious", "zh": "贵金属", "en": "Precious Metals", "codes": ["au", "ag"]},
    {"key": "energy", "zh": "能源", "en": "Energy", "codes": ["sc", "lu", "fu", "bu", "nr"]},
    {"key": "chemicals", "zh": "化工", "en": "Chemicals", "codes": ["ru", "br", "l", "pp", "v", "eb", "eg", "pg", "ta", "ma", "fg", "sa", "ur", "sp"]},
    {"key": "oils_meals", "zh": "油脂油料", "en": "Oils & Meals", "codes": ["p", "y", "oi", "m", "rm", "a", "b"]},
    {"key": "grains", "zh": "谷物淀粉", "en": "Grains & Starch", "codes": ["c", "cs"]},
    {"key": "softs", "zh": "软商品", "en": "Softs", "codes": ["cf", "sr", "ap", "cj", "pk"]},
    {"key": "livestock", "zh": "畜禽", "en": "Livestock", "codes": ["jd", "lh"]},
    {"key": "financials", "zh": "金融期货", "en": "Financial Futures", "codes": ["if", "ih", "ic", "im", "ts", "tf", "t", "tl"]},
]

DEFAULT_MAIN_CONTRACTS: list[str] = [
    "SHFE.rb2510",
    "SHFE.hc2510",
    "DCE.i2509",
    "DCE.j2509",
    "DCE.jm2509",
    "CZCE.SF509",
    "CZCE.SM509",
    "SHFE.cu2509",
    "SHFE.al2509",
    "SHFE.zn2509",
    "SHFE.pb2509",
    "SHFE.ni2509",
    "SHFE.sn2509",
    "SHFE.ss2509",
    "SHFE.ao2509",
    "INE.bc2509",
    "SHFE.au2508",
    "SHFE.ag2508",
    "INE.sc2509",
    "INE.lu2509",
    "SHFE.fu2509",
    "SHFE.bu2509",
    "SHFE.nr2509",
    "SHFE.ru2509",
    "SHFE.br2509",
    "DCE.l2509",
    "DCE.pp2509",
    "DCE.v2509",
    "DCE.eb2509",
    "DCE.eg2509",
    "DCE.pg2509",
    "CZCE.TA509",
    "CZCE.MA509",
    "CZCE.FG509",
    "CZCE.SA509",
    "CZCE.UR509",
    "SHFE.sp2509",
    "DCE.p2509",
    "DCE.y2509",
    "CZCE.OI509",
    "DCE.m2509",
    "CZCE.RM509",
    "DCE.a2509",
    "DCE.b2509",
    "DCE.c2509",
    "DCE.cs2509",
    "CZCE.CF509",
    "CZCE.SR509",
    "CZCE.AP510",
    "CZCE.CJ509",
    "CZCE.PK509",
    "DCE.jd2509",
    "DCE.lh2509",
    "CFFEX.IF2506",
    "CFFEX.IH2506",
    "CFFEX.IC2506",
    "CFFEX.IM2506",
    "CFFEX.TS2506",
    "CFFEX.TF2506",
    "CFFEX.T2506",
    "CFFEX.TL2506",
]


def _split_contract_token(symbol: str) -> tuple[str, str] | None:
    match = re.match(r"^([A-Za-z]+)(\d+)$", symbol.strip())
    if not match:
        return None
    return match.group(1), match.group(2)


def _build_contract_exchange_index() -> dict[str, tuple[str, str]]:
    index: dict[str, tuple[str, str]] = {}
    for full_symbol in DEFAULT_MAIN_CONTRACTS:
        _, _, instrument = full_symbol.partition(".")
        parts = _split_contract_token(instrument)
        if parts is None:
            continue
        prefix, _ = parts
        index.setdefault(prefix.lower(), (full_symbol.split(".", 1)[0], prefix))
    return index


CONTRACT_EXCHANGE_INDEX = _build_contract_exchange_index()
SUPPORTED_MAIN_CONTRACT_CODES = {
    code.lower()
    for category in MAIN_CONTRACT_CATEGORIES
    for code in category["codes"]
}
PREFERRED_QUOTE_CODES = ("rb", "i", "m", "cf", "ma")


def normalize_contract_symbol(symbol: str) -> str:
    raw_symbol = str(symbol or "").strip()
    if not raw_symbol:
        return raw_symbol

    if "." in raw_symbol:
        exchange, _, instrument = raw_symbol.partition(".")
        parts = _split_contract_token(instrument)
        if parts is None:
            return f"{exchange.upper()}.{instrument}"
        prefix, digits = parts
        mapped = CONTRACT_EXCHANGE_INDEX.get(prefix.lower())
        if mapped is None:
            return f"{exchange.upper()}.{prefix}{digits}"
        normalized_exchange, canonical_prefix = mapped
        return f"{normalized_exchange}.{canonical_prefix}{digits}"

    parts = _split_contract_token(raw_symbol)
    if parts is None:
        return raw_symbol
    prefix, digits = parts
    mapped = CONTRACT_EXCHANGE_INDEX.get(prefix.lower())
    if mapped is None:
        return raw_symbol
    exchange, canonical_prefix = mapped
    return f"{exchange}.{canonical_prefix}{digits}"


def _extract_contract_code(symbol: str) -> str:
    raw_symbol = str(symbol or "").strip()
    if not raw_symbol:
        return ""

    if "@" in raw_symbol:
        raw_symbol = raw_symbol.rsplit("@", 1)[-1]
    if "." in raw_symbol:
        raw_symbol = raw_symbol.split(".", 1)[1]

    match = re.match(r"^([A-Za-z]+)", raw_symbol)
    if not match:
        return ""
    return match.group(1).lower()


def _read_object_field(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            value = obj.get(name)
        else:
            value = getattr(obj, name, None)
        if value is not None:
            return value
    return default


def _safe_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        coerced = float(value)
    except (TypeError, ValueError):
        return None
    if coerced != coerced:
        return None
    return coerced


def _dedupe_contracts(contracts: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for contract in contracts:
        normalized = normalize_contract_symbol(contract)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _call_tqsdk_query_quotes(api: Any, **kwargs: Any) -> list[str]:
    query_quotes = getattr(api, "query_quotes", None)
    if not callable(query_quotes):
        return []

    for candidate_kwargs in (kwargs, {key: value for key, value in kwargs.items() if key != "expired"}):
        try:
            result = query_quotes(**candidate_kwargs)
        except TypeError:
            continue
        except Exception:
            return []
        if result:
            return [str(item) for item in result if item]
    return []


def _wait_tqsdk_quote_data(api: Any, cycles: int = 2) -> None:
    wait_update = getattr(api, "wait_update", None)
    if not callable(wait_update):
        return

    for _ in range(max(1, cycles)):
        try:
            wait_update(deadline=time.time() + 1.0)
        except TypeError:
            try:
                wait_update()
            except Exception:
                break
        except Exception:
            break


def _fetch_main_contracts_from_cont_quotes(api: Any) -> list[str]:
    cont_symbols = _call_tqsdk_query_quotes(api, ins_class="CONT", expired=False)
    if not cont_symbols:
        return []

    subscribed = {
        symbol: api.get_quote(symbol)
        for symbol in cont_symbols
        if _extract_contract_code(symbol) in SUPPORTED_MAIN_CONTRACT_CODES
    }
    if not subscribed:
        return []

    _wait_tqsdk_quote_data(api)

    resolved_by_code: dict[str, str] = {}
    for symbol, quote in subscribed.items():
        code = _extract_contract_code(symbol)
        if not code:
            continue
        underlying_symbol = _read_object_field(
            quote,
            "underlying_symbol",
            "underlying_symbol1",
            "underlying_symbol0",
        )
        if not underlying_symbol:
            continue
        resolved_by_code[code] = normalize_contract_symbol(str(underlying_symbol))

    contracts = [
        resolved_by_code[code.lower()]
        for category in MAIN_CONTRACT_CATEGORIES
        for code in category["codes"]
        if code.lower() in resolved_by_code
    ]
    return _dedupe_contracts(contracts)


def _quote_liquidity_score(quote: Any) -> tuple[float, float, float]:
    open_interest = _safe_float(_read_object_field(quote, "open_interest", "open_interest1"))
    volume = _safe_float(_read_object_field(quote, "volume"))
    last_price = _safe_float(_read_object_field(quote, "last_price", "last"))
    return (
        open_interest if open_interest is not None else -1.0,
        volume if volume is not None else -1.0,
        last_price if last_price is not None else -1.0,
    )


def _fetch_main_contracts_from_futures_quotes(api: Any) -> list[str]:
    future_symbols = _call_tqsdk_query_quotes(api, ins_class="FUTURE", expired=False)
    if not future_symbols:
        return []

    candidates = [
        str(symbol)
        for symbol in future_symbols
        if _extract_contract_code(symbol) in SUPPORTED_MAIN_CONTRACT_CODES
    ]
    if not candidates:
        return []

    subscribed = {symbol: api.get_quote(symbol) for symbol in candidates}
    _wait_tqsdk_quote_data(api)

    best_by_code: dict[str, tuple[tuple[float, float, float], str]] = {}
    for symbol, quote in subscribed.items():
        code = _extract_contract_code(symbol)
        if not code:
            continue
        score = _quote_liquidity_score(quote)
        existing = best_by_code.get(code)
        normalized_symbol = normalize_contract_symbol(symbol)
        if existing is None or score > existing[0]:
            best_by_code[code] = (score, normalized_symbol)

    contracts = [
        best_by_code[code.lower()][1]
        for category in MAIN_CONTRACT_CATEGORIES
        for code in category["codes"]
        if code.lower() in best_by_code
    ]
    return _dedupe_contracts(contracts)


def _select_realtime_quote_symbols(live_contracts: list[str]) -> list[str]:
    by_code = {
        _extract_contract_code(contract): normalize_contract_symbol(contract)
        for contract in live_contracts
        if _extract_contract_code(contract)
    }

    selected: list[str] = []
    for code in PREFERRED_QUOTE_CODES:
        symbol = by_code.get(code)
        if symbol and symbol not in selected:
            selected.append(symbol)
    for contract in live_contracts:
        normalized = normalize_contract_symbol(contract)
        if normalized not in selected:
            selected.append(normalized)
        if len(selected) >= 5:
            break
    return selected[:5]


def _fetch_realtime_quotes(api: Any, symbols: list[str]) -> list[dict[str, Any]]:
    subscribed = {normalize_contract_symbol(symbol): api.get_quote(symbol) for symbol in symbols if symbol}
    if not subscribed:
        return []

    _wait_tqsdk_quote_data(api)

    quotes: list[dict[str, Any]] = []
    for symbol, quote in subscribed.items():
        price = _safe_float(_read_object_field(quote, "last_price", "last", "price"))
        reference = _safe_float(_read_object_field(quote, "pre_close", "pre_settlement", "open"))
        if price is None:
            continue
        if reference is not None and abs(reference) > 1e-9:
            change = round((price - reference) / reference * 100, 2)
        else:
            change = 0.0
        quotes.append(
            {
                "symbol": symbol,
                "price": round(price, 4),
                "last": round(price, 4),
                "change": change,
                "source": "tqsdk_realtime_quotes",
            }
        )
    return quotes


def _build_tqsdk_market_snapshot() -> tuple[Optional[dict[str, Any]], str]:
    settings = get_settings()
    if not settings.tqsdk_auth_username or not settings.tqsdk_auth_password:
        return None, "tqsdk_auth_not_configured"

    try:
        from tqsdk import TqApi, TqAuth
    except Exception as exc:
        return None, f"tqsdk_import_failed:{exc.__class__.__name__}"

    try:
        auth = TqAuth(settings.tqsdk_auth_username, settings.tqsdk_auth_password)
    except Exception as exc:
        return None, f"tqsdk_auth_failed:{exc.__class__.__name__}"

    api = None
    try:
        api_kwargs: dict[str, Any] = {"disable_print": True}
        if auth is not None:
            api_kwargs["auth"] = auth
        api = TqApi(**api_kwargs)

        live_contracts = _fetch_main_contracts_from_cont_quotes(api)
        if not live_contracts:
            live_contracts = _fetch_main_contracts_from_futures_quotes(api)
        if not live_contracts:
            return None, "tqsdk_main_contracts_unavailable"

        live_quotes = _fetch_realtime_quotes(api, _select_realtime_quote_symbols(live_contracts))
        return {
            "main_contracts": live_contracts,
            "quotes": live_quotes,
            "source": "tqsdk_realtime_main_contracts",
            "note": "TqSdk 实时主力合约清单；查询失败时会自动回退到本地兼容清单。",
        }, ""
    except Exception as exc:
        return None, f"tqsdk_market_snapshot_failed:{exc.__class__.__name__}"
    finally:
        if api is not None:
            close = getattr(api, "close", None)
            if callable(close):
                close()


def _get_tqsdk_market_snapshot(state: dict[str, Any]) -> Optional[dict[str, Any]]:
    cache = state.get("tqsdk_market_cache") or {}
    fetched_at = int(cache.get("fetched_at") or 0)
    now = _now_ts()
    if now - fetched_at < MARKET_CACHE_TTL_SECONDS:
        snapshot = cache.get("snapshot")
        if isinstance(snapshot, Mapping):
            return dict(snapshot)
        return None

    snapshot, error = _build_tqsdk_market_snapshot()
    state["tqsdk_market_cache"] = {
        "fetched_at": now,
        "snapshot": dict(snapshot) if isinstance(snapshot, Mapping) else None,
        "error": error,
    }
    if isinstance(snapshot, Mapping):
        return dict(snapshot)
    return None


def _now_ts() -> int:
    return int(time.time())


def _clock_text(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).astimezone().strftime("%m-%d %H:%M:%S")


def _format_uptime(seconds: int) -> str:
    hours, remainder = divmod(max(0, int(seconds)), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _strip_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"\"", "'"}:
        return text[1:-1]
    return text


def _strip_inline_comment(value: str) -> str:
    text = _strip_quotes(value)
    candidate = re.sub(r"\s+#.*$", "", text).strip()
    return candidate or text


def _parse_scalar(value: str) -> Any:
    text = _strip_inline_comment(value)
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if any(char in text for char in (".", "e", "E")):
            return float(text)
        return int(text)
    except ValueError:
        return text


def _sanitize_loaded_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _sanitize_loaded_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_loaded_payload(item) for item in value]
    if isinstance(value, str) and "#" in value:
        return _parse_scalar(value)
    return value


def _parse_inline_list(value: str) -> list[str]:
    text = value.strip()
    if not text.startswith("[") or not text.endswith("]"):
        return []
    items = []
    for raw_item in text[1:-1].split(","):
        item = _strip_quotes(raw_item)
        if item:
            items.append(item)
    return items


def _extract_top_level_scalar(content: str, key: str) -> Any:
    match = re.search(rf"^{key}:\s*(.+)$", content, flags=re.MULTILINE)
    if not match:
        return ""
    return _parse_scalar(match.group(1))


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in {None, ""}:
            return value
    return ""


def _extract_section_scalars(content: str, section: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    in_section = False

    for line in content.splitlines():
        if re.match(rf"^{section}:\s*$", line):
            in_section = True
            continue
        if not in_section:
            continue
        if line and not line.startswith(" "):
            break
        match = re.match(r"^\s{2}([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+)$", line)
        if match:
            values[match.group(1)] = _parse_scalar(match.group(2))

    return values


def _extract_symbols(content: str) -> list[str]:
    symbols: list[str] = []
    active_symbols_indent: Optional[int] = None

    for line in content.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue

        inline_list = re.match(r"^\s*symbols:\s*(\[.*\])\s*$", line)
        if inline_list:
            symbols.extend(_parse_inline_list(inline_list.group(1)))
            continue

        single_symbol = re.match(r"^\s*symbol:\s*(.+)$", line)
        if single_symbol:
            symbol = _strip_quotes(single_symbol.group(1))
            if symbol:
                symbols.append(symbol)
            continue

        symbols_block = re.match(r"^(\s*)symbols:\s*$", line)
        if symbols_block:
            active_symbols_indent = len(symbols_block.group(1))
            continue

        if active_symbols_indent is not None:
            current_indent = len(line) - len(line.lstrip(" "))
            if current_indent <= active_symbols_indent:
                active_symbols_indent = None
            else:
                item = re.match(r"^\s*-\s*(.+)$", line)
                if item:
                    symbol = _strip_quotes(item.group(1))
                    if symbol:
                        symbols.append(symbol)
                    continue

    deduped: list[str] = []
    seen = set()
    for symbol in symbols:
        if symbol not in seen:
            seen.add(symbol)
            deduped.append(symbol)
    return deduped


def _extract_strategy_metadata(name: str, content: str) -> dict[str, Any]:
    strategy_params = _extract_section_scalars(content, "strategy")
    parameter_params = _extract_section_scalars(content, "parameters")
    signal_params = _extract_section_scalars(content, "signal")
    risk_params = _extract_section_scalars(content, "risk")
    transaction_costs = _extract_section_scalars(content, "transaction_costs")
    factor_names = [_strip_quotes(raw_name) for raw_name in re.findall(r"^\s*factor_name:\s*(.+)$", content, flags=re.MULTILINE)]
    indicator_names = [_strip_quotes(raw_name) for raw_name in re.findall(r"^\s*-\s*name:\s*(.+)$", content, flags=re.MULTILINE)]

    flat_params: dict[str, Any] = {}
    flat_params.update(parameter_params)
    flat_params.update(transaction_costs)
    flat_params.update(signal_params)
    flat_params.update(risk_params)

    timeframe_minutes = _first_non_empty(
        flat_params.get("timeframe_minutes"),
        flat_params.get("timeframe"),
        _extract_top_level_scalar(content, "timeframe_minutes"),
        _extract_top_level_scalar(content, "timeframe"),
    )
    if timeframe_minutes not in {"", None}:
        flat_params["timeframe_minutes"] = timeframe_minutes
        flat_params.setdefault("timeframe", timeframe_minutes)

    description = _first_non_empty(_extract_top_level_scalar(content, "description"), strategy_params.get("description"))
    category = _first_non_empty(_extract_top_level_scalar(content, "category"), strategy_params.get("category"))
    template_id = _first_non_empty(_extract_top_level_scalar(content, "template_id"), strategy_params.get("template_id"))
    version = _first_non_empty(_extract_top_level_scalar(content, "version"), strategy_params.get("version"))

    merged_factor_names: list[str] = []
    for raw_name in [*factor_names, *indicator_names]:
      if raw_name and raw_name not in merged_factor_names:
          merged_factor_names.append(raw_name)

    return {
        "description": "" if description in {None, ""} else str(description),
        "category": "" if category in {None, ""} else str(category),
        "template_id": "" if template_id in {None, ""} else str(template_id),
        "version": "" if version in {None, ""} else str(version),
        "symbols": _extract_symbols(content),
        "factor_names": merged_factor_names,
        "params": flat_params,
    }


def _build_definition_metadata(definition: Any) -> dict[str, Any]:
    metadata = dict(definition.metadata)
    params = dict(definition.params)
    if definition.timeframe_minutes is not None:
        params.setdefault("timeframe_minutes", definition.timeframe_minutes)
        params.setdefault("timeframe", definition.timeframe_minutes)

    factor_names: list[str] = []
    for factor in definition.factors:
        if factor.factor_name and factor.factor_name not in factor_names:
            factor_names.append(factor.factor_name)
    for indicator in definition.indicators:
        if indicator.name and indicator.name not in factor_names:
            factor_names.append(indicator.name)

    return {
        "description": str(metadata.get("description") or "").strip(),
        "category": str(metadata.get("category") or "").strip(),
        "template_id": definition.template_id,
        "version": str(metadata.get("version") or "").strip(),
        "symbols": list(definition.symbols),
        "factor_names": factor_names,
        "params": params,
        "capital_params": dict(definition.capital_params),
        "signal": dict(definition.signal),
        "risk": definition.risk.as_snapshot(),
    }


def _normalize_strategy_yaml_filename(name: str) -> str:
    base_name = Path(name).name.strip()
    if not base_name:
        return "strategy.yaml"
    if Path(base_name).suffix:
        return base_name
    return f"{base_name}.yaml"


def _persist_strategy_yaml(name: str, content: str) -> tuple[str, Path]:
    settings = get_settings()
    strategy_root = settings.tqsdk_strategy_yaml_dir.expanduser().resolve()
    strategy_root.mkdir(parents=True, exist_ok=True)

    file_name = _normalize_strategy_yaml_filename(name)
    target_path = (strategy_root / file_name).resolve()
    if strategy_root not in target_path.parents:
        raise ValueError("strategy YAML target must stay within TQSDK_STRATEGY_YAML_DIR")

    target_path.write_text(content, encoding="utf-8")
    return file_name, target_path


def _build_formal_engine_status() -> dict[str, Any]:
    settings = get_settings()
    registered_templates: list[str] = []
    if strategy_registry is not None:
        try:
            registered_templates = list(strategy_registry.list_template_ids())
        except Exception:
            registered_templates = []

    auth_configured = bool(settings.tqsdk_auth_username and settings.tqsdk_auth_password)
    ready = auth_configured and settings.backtest_mode == "online"
    reason = "正式引擎已具备基础运行条件" if ready else "正式引擎未完成 TQSDK 认证配置，当前只能执行兼容预览"

    return {
        "ready": ready,
        "auth_configured": auth_configured,
        "backtest_mode": settings.backtest_mode,
        "registered_templates": registered_templates,
        "reason": reason,
    }


def _scan_strategy_metadata(
    metadata: dict[str, Any],
    raw_payload: Mapping[str, Any],
    formal_parser_error: Optional[str],
    definition: Any,
) -> dict[str, Any]:
    """Scan imported strategy and return a diagnostic summary."""
    registered_factor_names: set[str] = set()
    if _factor_registry is not None:
        try:
            registered_factor_names = set(_factor_registry.list_factors())
        except Exception:
            pass

    factor_names = list(metadata.get("factor_names") or [])
    missing_factors = []
    for f in factor_names:
        if not f or not f.strip():
            continue
        try:
            if _factor_registry is not None:
                _factor_registry.resolve_factor_name(f)
        except Exception:
            missing_factors.append(f)

    has_transaction_costs = False
    if definition is not None:
        tc = getattr(definition, "transaction_costs", {}) or {}
        has_transaction_costs = bool(tc.get("slippage_per_unit") is not None or tc.get("commission_per_lot_round_turn") is not None)
    else:
        tc_section = raw_payload.get("transaction_costs") or {}
        has_transaction_costs = bool(tc_section)

    has_stop_loss = False
    has_take_profit = False
    if definition is not None:
        risk_snapshot = {}
        try:
            risk_snapshot = definition.risk.as_snapshot()
        except Exception:
            pass
        has_stop_loss = bool(
            risk_snapshot.get("stop_loss_atr")
            or (risk_snapshot.get("stop_loss") or {}).get("atr_multiplier")
            or risk_snapshot.get("stop_loss_atr_multiplier")
        )
        has_take_profit = bool(
            risk_snapshot.get("take_profit_atr")
            or (risk_snapshot.get("take_profit") or {}).get("atr_multiplier")
            or risk_snapshot.get("take_profit_atr_multiplier")
        )
    else:
        risk_section = raw_payload.get("risk") or {}
        if isinstance(risk_section, Mapping):
            has_stop_loss = bool(
                risk_section.get("stop_loss_atr")
                or (risk_section.get("stop_loss") or {}).get("atr_multiplier")
                or risk_section.get("stop_loss_atr_multiplier")
            )
            has_take_profit = bool(
                risk_section.get("take_profit_atr")
                or (risk_section.get("take_profit") or {}).get("atr_multiplier")
                or risk_section.get("take_profit_atr_multiplier")
            )

    warnings = []
    if not has_transaction_costs:
        warnings.append("transaction_costs 未配置，将使用零成本默认值")
    if not has_stop_loss:
        warnings.append("未配置止损 (risk.stop_loss_atr 或 risk.stop_loss.atr_multiplier)")
    if not has_take_profit:
        warnings.append("未配置止盈 (risk.take_profit_atr 或 risk.take_profit.atr_multiplier)")

    if missing_factors:
        warnings.append(f"因子未注册（可能在运行时动态加载）：{', '.join(missing_factors)}")

    if formal_parser_error:
        scan_status = "blocked"
    else:
        scan_status = "warning" if (warnings or missing_factors) else "ready"

    return {
        "scan_status": scan_status,
        "missing_factors": missing_factors,
        "has_transaction_costs": has_transaction_costs,
        "has_stop_loss": has_stop_loss,
        "has_take_profit": has_take_profit,
        "warnings": warnings,
        "formal_parser_error": formal_parser_error,
        "scanned_at": _now_ts(),
    }


def _normalize_strategy_yaml(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    自动格式归一化：将用户自定义字段名转换为引擎标准字段名。
    返回 (归一化后的 dict, 转换说明列表)。
    """
    warnings: list[str] = []
    d = dict(raw)

    # ── signal_rules → signal ──────────────────────────────────────
    if "signal_rules" in d and "signal" not in d:
        sr = d.pop("signal_rules")
        if isinstance(sr, Mapping):
            signal: dict[str, Any] = {}
            for src, dst in (("entry_long", "long_condition"), ("entry_short", "short_condition"),
                             ("exit_long", "long_exit"), ("exit_short", "short_exit")):
                if src in sr:
                    raw_expr = str(sr[src])
                    # YAML > 折叠会把注释行和表达式折成同一行，如：
                    # "# 趋势注释 (ma20 > ma60) and # ADX注释 (adx >= 20)"
                    # 用正则去除所有 "#中文注释 " 片段（从#到下一个(之前）
                    clean_expr = re.sub(r"#[^(\n]*", "", raw_expr)
                    # 清理多余空白
                    clean_expr = re.sub(r"\s+", " ", clean_expr).strip()
                    if clean_expr:
                        signal[dst] = clean_expr
            d["signal"] = signal
            warnings.append("signal_rules → signal")

    # ── signal.long_threshold / short_threshold → long_condition / short_condition ──
    signal_block = d.get("signal")
    if isinstance(signal_block, Mapping):
        has_long_condition = bool(signal_block.get("long_condition"))
        has_short_condition = bool(signal_block.get("short_condition"))
        long_threshold = signal_block.get("long_threshold")
        short_threshold = signal_block.get("short_threshold")
        if not has_long_condition and long_threshold is not None:
            sig = dict(signal_block)
            sig["long_condition"] = f"factor_total_score >= {long_threshold}"
            if not has_short_condition and short_threshold is not None:
                sig["short_condition"] = f"factor_total_score <= {short_threshold}"
            d["signal"] = sig
            warnings.append(f"signal.long_threshold={long_threshold} → long_condition (factor_total_score)")

    def normalize_indicator_params(factor_name: Any, params_raw: Any) -> dict[str, Any]:
        if isinstance(params_raw, Mapping):
            return dict(params_raw)
        if not isinstance(params_raw, list):
            return {}

        fn_upper = str(factor_name or "").strip().upper()
        params_dict: dict[str, Any] = {}
        string_values = [value for value in params_raw if isinstance(value, str)]
        numeric_values = [
            value
            for value in params_raw
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ]

        def assign_ohlc(keys: list[str]) -> None:
            for key, value in zip(keys, string_values):
                params_dict[key] = value

        if fn_upper in {
            "SMA",
            "EMA",
            "RSI",
            "VOLUMERATIO",
            "VOLUME_RATIO",
            "WMA",
            "HMA",
            "TEMA",
            "ROC",
            "MOM",
            "CMO",
            "DEMA",
            "EMA_SLOPE",
            "HISTORICALVOL",
            "HISTVOL",
            "STDEV",
            "ZSCORE",
            "DPO",
            "LINREG",
        }:
            if string_values:
                params_dict["source"] = string_values[0]
            if numeric_values:
                params_dict["period"] = numeric_values[0]
        elif fn_upper == "MACD":
            if string_values:
                params_dict["source"] = string_values[0]
            if len(numeric_values) >= 1:
                params_dict["fast"] = numeric_values[0]
            if len(numeric_values) >= 2:
                params_dict["slow"] = numeric_values[1]
            if len(numeric_values) >= 3:
                params_dict["signal"] = numeric_values[2]
        elif fn_upper == "EMA_CROSS":
            if string_values:
                params_dict["source"] = string_values[0]
            if len(numeric_values) >= 1:
                params_dict["fast_period"] = numeric_values[0]
            if len(numeric_values) >= 2:
                params_dict["slow_period"] = numeric_values[1]
        elif fn_upper in {"ATR", "ADX", "NTR", "BULLBEARPOWER"}:
            assign_ohlc(["high", "low", "close"])
            if numeric_values:
                params_dict["period"] = numeric_values[0]
        elif fn_upper in {"STOCHASTIC", "KDJ", "WILLIAMSR", "CCI"}:
            assign_ohlc(["high", "low", "close"])
            if numeric_values:
                params_dict["period"] = numeric_values[0]
            if fn_upper == "STOCHASTIC":
                if len(numeric_values) >= 1:
                    params_dict["k_period"] = numeric_values[0]
                if len(numeric_values) >= 2:
                    params_dict["d_period"] = numeric_values[1]
                if len(numeric_values) >= 3:
                    params_dict["smooth_k"] = numeric_values[2]
            elif fn_upper == "KDJ":
                if len(numeric_values) >= 1:
                    params_dict["k_period"] = numeric_values[0]
                if len(numeric_values) >= 2:
                    params_dict["d_period"] = numeric_values[1]
                if len(numeric_values) >= 3:
                    params_dict["j_smooth"] = numeric_values[2]
        elif fn_upper == "STOCHASTICRSI":
            if string_values:
                params_dict["source"] = string_values[0]
            if len(numeric_values) >= 1:
                params_dict["rsi_period"] = numeric_values[0]
            if len(numeric_values) >= 2:
                params_dict["stoch_period"] = numeric_values[1]
            if len(numeric_values) >= 3:
                params_dict["k_period"] = numeric_values[2]
            if len(numeric_values) >= 4:
                params_dict["d_period"] = numeric_values[3]
        elif fn_upper in {"BOLLINGERBANDS", "TRIX"}:
            if string_values:
                params_dict["source"] = string_values[0]
            if numeric_values:
                params_dict["period"] = numeric_values[0]
            if fn_upper == "BOLLINGERBANDS" and len(numeric_values) >= 2:
                params_dict["std_dev"] = numeric_values[1]
            if fn_upper == "TRIX" and len(numeric_values) >= 2:
                params_dict["signal"] = numeric_values[1]
        elif fn_upper == "DONCHIANBREAKOUT":
            assign_ohlc(["high", "low"])
            if numeric_values:
                params_dict["entry_period"] = numeric_values[0]
            if len(numeric_values) >= 2:
                params_dict["exit_period"] = numeric_values[1]
        elif fn_upper in {"VWAP", "CHAIKINAD"}:
            assign_ohlc(["high", "low", "close", "volume"])
        elif fn_upper in {"MFI", "CMF"}:
            assign_ohlc(["high", "low", "close", "volume"])
            if numeric_values:
                params_dict["period"] = numeric_values[0]
        elif fn_upper in {"OBV", "PVT"}:
            assign_ohlc(["close", "volume"])
        elif fn_upper == "KELTNERCHANNEL":
            assign_ohlc(["high", "low", "close"])
            if numeric_values:
                params_dict["ema_period"] = numeric_values[0]
            if len(numeric_values) >= 2:
                params_dict["atr_period"] = numeric_values[1]
            if len(numeric_values) >= 3:
                params_dict["multiplier"] = numeric_values[2]
        elif fn_upper == "AROON":
            assign_ohlc(["high", "low"])
            if numeric_values:
                params_dict["period"] = numeric_values[0]
        elif fn_upper == "ATRTRAILINGSTOP":
            assign_ohlc(["high", "low", "close"])
            if numeric_values:
                params_dict["period"] = numeric_values[0]
            if len(numeric_values) >= 2:
                params_dict["multiplier"] = numeric_values[1]
        elif fn_upper == "SUPERTREND":
            assign_ohlc(["high", "low", "close"])
            if numeric_values:
                params_dict["period"] = numeric_values[0]
            if len(numeric_values) >= 2:
                params_dict["multiplier"] = numeric_values[1]
        elif fn_upper == "PARABOLICSAR":
            assign_ohlc(["high", "low", "close"])
            if numeric_values:
                params_dict["af_start"] = numeric_values[0]
            if len(numeric_values) >= 2:
                params_dict["af_max"] = numeric_values[1]
        elif fn_upper == "ICHIMOKU":
            assign_ohlc(["high", "low", "close"])
            if numeric_values:
                params_dict["tenkan"] = numeric_values[0]
            if len(numeric_values) >= 2:
                params_dict["kijun"] = numeric_values[1]
            if len(numeric_values) >= 3:
                params_dict["senkou_b"] = numeric_values[2]
        else:
            if numeric_values:
                params_dict["period"] = numeric_values[0]
            if string_values:
                params_dict["source"] = string_values[0]

        return params_dict

    # ── indicators → factors (type/params 格式) ───────────────────
    if "indicators" in d and "factors" not in d:
        raw_inds = d.pop("indicators")
        if isinstance(raw_inds, list):
            factors = []
            for ind in raw_inds:
                if not isinstance(ind, Mapping):
                    continue
                fn = ind.get("type") or ind.get("factor_name") or ind.get("name", "")
                params_raw = ind.get("params", [])
                params_dict = normalize_indicator_params(fn, params_raw)
                alias_name = str(ind.get("alias") or ind.get("name") or "").strip()
                factor_name = str(fn or "").strip()
                if alias_name and alias_name != factor_name:
                    params_dict["_alias"] = alias_name
                factors.append({
                    "factor_name": fn,
                    "weight": ind.get("weight", 1.0),
                    "params": params_dict,
                })
            d["factors"] = factors
            warnings.append("indicators → factors")

    # ── factors: normalize list-style params to mapping ─────────
    if "factors" in d:
        raw_factors = d.get("factors")
        if isinstance(raw_factors, list):
            normalized_factors = []
            changed = False
            for factor in raw_factors:
                if not isinstance(factor, Mapping):
                    normalized_factors.append(factor)
                    continue
                params_raw = factor.get("params")
                if isinstance(params_raw, list):
                    fn = factor.get("factor_name") or factor.get("name") or ""
                    params_dict = normalize_indicator_params(fn, params_raw)
                    new_factor = dict(factor)
                    new_factor["params"] = params_dict
                    normalized_factors.append(new_factor)
                    changed = True
                else:
                    normalized_factors.append(dict(factor))
            if changed:
                d["factors"] = normalized_factors
                warnings.append("factors.params list→mapping")

    # ── position_size → position_fraction ────────────────────────
    if "position_size" in d and "position_fraction" not in d:
        ps = d.pop("position_size")
        if isinstance(ps, Mapping):
            frac = ps.get("fraction") or ps.get("position_fraction")
            if frac is not None:
                d["position_fraction"] = float(frac)
            warnings.append("position_size → position_fraction")

    # ── trading_cost → transaction_costs ─────────────────────────
    if "trading_cost" in d and "transaction_costs" not in d:
        tc = d.pop("trading_cost")
        if isinstance(tc, Mapping):
            d["transaction_costs"] = {
                "slippage_per_unit": tc.get("slippage", tc.get("slippage_per_unit", 0)),
                "commission_per_lot_round_turn": tc.get("commission", tc.get("commission_per_lot_round_turn", 0)),
            }
            warnings.append("trading_cost → transaction_costs")

    # ── risk_management → risk ────────────────────────────────────
    if "risk_management" in d and "risk" not in d:
        rm = d.pop("risk_management")
        if isinstance(rm, Mapping):
            risk: dict[str, Any] = {}
            # 日内熔断：绝对金额自动转比例（若 initial_capital 可知则精确，否则用保守估算）
            if "daily_loss_limit" in rm:
                v = rm["daily_loss_limit"]
                if isinstance(v, (int, float)) and v > 1:
                    # 判定为金额而非比例，尝试从 capital_params 或 100000 估算
                    cap = 100000.0
                    pos_size = d.get("position_size", {})
                    max_pos_val = pos_size.get("max_position_value") if isinstance(pos_size, Mapping) else None
                    if max_pos_val:
                        cap = float(max_pos_val) / (d.get("position_fraction") or 0.4)
                    risk["daily_loss_limit"] = round(float(v) / cap, 4)
                    warnings.append(f"risk_management.daily_loss_limit {v}(金额)→{risk['daily_loss_limit']}(比例,估算资金{cap:.0f})")
                else:
                    risk["daily_loss_limit"] = float(v)
            if "total_period_loss_limit" in rm:
                v = rm["total_period_loss_limit"]
                if isinstance(v, (int, float)) and v > 1:
                    cap = 100000.0
                    risk["max_drawdown_pct"] = round(float(v) / cap, 4)
                    warnings.append(f"risk_management.total_period_loss_limit {v}(金额)→max_drawdown_pct {risk['max_drawdown_pct']}")
                else:
                    risk["max_drawdown_pct"] = float(v)
            # 止损/止盈：百分比固定止损转为近似 ATR 倍数（用原始值记录备注）
            if "stop_loss_percentage" in rm:
                risk.setdefault("stop_loss", {"atr_multiplier": 1.5, "type": "atr"})
                warnings.append(f"stop_loss_percentage={rm['stop_loss_percentage']} → stop_loss.atr_multiplier=1.5(已保留,如需精确请手动指定 atr_multiplier)")
            if "take_profit_percentage" in rm:
                risk.setdefault("take_profit", {"atr_multiplier": 3.0, "type": "atr"})
                warnings.append(f"take_profit_percentage={rm['take_profit_percentage']} → take_profit.atr_multiplier=3.0(已保留)")
            # 强平时间
            for src, dst in (("end_time", "force_close_day"), ("force_close_day", "force_close_day")):
                if src in rm and "force_close_day" not in risk:
                    risk["force_close_day"] = rm[src]
            risk.setdefault("force_close_night", "22:55")
            risk.setdefault("no_overnight", False)
            # 其他直通字段
            for key in ("max_drawdown_pct", "max_drawdown", "no_overnight", "stop_loss", "take_profit", "trailing_stop"):
                if key in rm and key not in risk:
                    risk[key] = rm[key]
            d["risk"] = risk
            warnings.append("risk_management → risk")

    # ── session_control.end_time → risk.force_close_day ──────────
    if "session_control" in d:
        sc = d.pop("session_control")
        if isinstance(sc, Mapping):
            risk_block = d.setdefault("risk", {})
            if isinstance(risk_block, Mapping):
                if "end_time" in sc and "force_close_day" not in risk_block:
                    risk_block["force_close_day"] = sc["end_time"]
                    warnings.append(f"session_control.end_time → risk.force_close_day")
            warnings.append("session_control → 已合并")

    # ── risk.force_close_night 缺失时自动补充 ────────────────────
    risk_block = d.get("risk")
    if isinstance(risk_block, Mapping) and "force_close_night" not in risk_block:
        risk_block["force_close_night"] = "22:55"
        warnings.append("risk.force_close_night 缺失，自动补充 22:55")

    # ── risk 字段名 _yuan/_pct 后缀归一化 ─────────────────────────
    risk_block = d.get("risk")
    if isinstance(risk_block, Mapping):
        # daily_loss_limit_yuan → daily_loss_limit（带金额→比例转换）
        if "daily_loss_limit_yuan" in risk_block and "daily_loss_limit" not in risk_block:
            risk_block["daily_loss_limit"] = risk_block.pop("daily_loss_limit_yuan")
            warnings.append("risk.daily_loss_limit_yuan → daily_loss_limit")
        # max_drawdown_pct → max_drawdown（已是比例，仅重命名）
        if "max_drawdown_pct" in risk_block and "max_drawdown" not in risk_block:
            risk_block["max_drawdown"] = risk_block.pop("max_drawdown_pct")
            warnings.append("risk.max_drawdown_pct → max_drawdown")
        # daily_loss_limit_pct → daily_loss_limit（已是比例，仅重命名）
        if "daily_loss_limit_pct" in risk_block and "daily_loss_limit" not in risk_block:
            risk_block["daily_loss_limit"] = risk_block.pop("daily_loss_limit_pct")
            warnings.append("risk.daily_loss_limit_pct → daily_loss_limit")

    # ── risk.daily_loss_limit 金额→比例自动转换 ──────────────────
    risk_block = d.get("risk")
    if isinstance(risk_block, Mapping):
        dll = risk_block.get("daily_loss_limit")
        if isinstance(dll, (int, float)) and not isinstance(dll, bool) and dll > 1:
            capital_params = d.get("capital_params", {})
            initial_capital = (capital_params.get("initial_capital") if isinstance(capital_params, Mapping) else None)
            cap = float(initial_capital) if initial_capital else 500000.0
            ratio = round(float(dll) / cap, 6)
            risk_block["daily_loss_limit"] = ratio
            warnings.append(f"risk.daily_loss_limit {dll}(金额)→{ratio}(比例,资金{cap:.0f})")
        mdd = risk_block.get("max_drawdown")
        if isinstance(mdd, (int, float)) and not isinstance(mdd, bool) and mdd > 1:
            capital_params = d.get("capital_params", {})
            initial_capital = (capital_params.get("initial_capital") if isinstance(capital_params, Mapping) else None)
            cap = float(initial_capital) if initial_capital else 500000.0
            ratio = round(float(mdd) / cap, 6)
            risk_block["max_drawdown"] = ratio
            warnings.append(f"risk.max_drawdown {mdd}(金额)→{ratio}(比例,资金{cap:.0f})")

    return d, warnings


def _load_strategy_record_metadata(name: str, content: str) -> tuple[str, dict[str, Any], Optional[str], dict[str, Any]]:
    try:
        raw_payload = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        raise ValueError("strategy YAML syntax is invalid") from exc
    if not isinstance(raw_payload, Mapping):
        raise ValueError("strategy YAML root must be a mapping")
    raw_payload = _sanitize_loaded_payload(raw_payload)

    # 自动归一化格式，将用户各种写法统一为引擎标准字段
    normalized_payload, norm_warnings = _normalize_strategy_yaml(dict(raw_payload))
    if norm_warnings:
        # 如果有转换，写回 YAML 文件内容
        content = "# [auto-normalized] " + ", ".join(norm_warnings) + "\n" + yaml.dump(
            normalized_payload, allow_unicode=True, default_flow_style=False, sort_keys=False
        )

    strategy_yaml_filename, strategy_yaml_path = _persist_strategy_yaml(name, content)
    metadata = _extract_strategy_metadata(name, content)
    formal_parser_error: Optional[str] = None
    definition = None

    if StrategyDefinition is not None:
        try:
            definition = StrategyDefinition.load(strategy_yaml_path)
        except StrategyConfigError as exc:
            formal_parser_error = str(exc)
        else:
            metadata = _build_definition_metadata(definition)

    scan_result = _scan_strategy_metadata(metadata, raw_payload, formal_parser_error, definition)
    return strategy_yaml_filename, metadata, formal_parser_error, scan_result


def _compose_strategy_record(
    *,
    name: str,
    content: str,
    existing: Optional[Mapping[str, Any]],
    now: int,
    strategy_yaml_filename: str,
    metadata: Mapping[str, Any],
    formal_parser_error: Optional[str],
    scan_result: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    existing_mapping = existing if isinstance(existing, Mapping) else {}
    capital_params = metadata.get("capital_params", existing_mapping.get("capital_params", {}))
    signal = metadata.get("signal", existing_mapping.get("signal", {}))
    risk = metadata.get("risk", existing_mapping.get("risk", {}))

    return {
        "id": re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "strategy",
        "name": name,
        "content": content,
        "strategy_yaml_filename": strategy_yaml_filename,
        "formal_parser_error": formal_parser_error,
        "scan_result": scan_result or {},
        "status": existing_mapping.get("status", "local"),
        "created_at": existing_mapping.get("created_at", now),
        "updated_at": now,
        "params": metadata["params"],
        "symbols": metadata["symbols"],
        "capital_params": capital_params,
        "signal": signal,
        "risk": risk,
        "strategy": {
            "id": name,
            "description": metadata["description"],
            "category": metadata["category"],
            "template_id": metadata["template_id"],
            "version": metadata["version"],
            "params": metadata["params"],
            "symbols": metadata["symbols"],
            "factor_names": metadata["factor_names"],
            "capital_params": capital_params,
            "signal": signal,
            "risk": risk,
            "strategy_yaml_filename": strategy_yaml_filename,
            "formal_parser_error": formal_parser_error,
        },
    }


def _autoload_persisted_strategies(state: dict[str, Any]) -> None:
    if state.get("_persisted_strategies_loaded"):
        return

    state["_persisted_strategies_loaded"] = True
    settings = get_settings()
    strategy_root = settings.tqsdk_strategy_yaml_dir.expanduser().resolve()
    if not strategy_root.exists():
        return

    loaded_count = 0
    seen_names: set[str] = set()
    for pattern in ("*.yaml", "*.yml"):
        for strategy_path in sorted(strategy_root.glob(pattern)):
            strategy_name = strategy_path.name
            if strategy_name in seen_names or strategy_name in state["strategies"]:
                continue
            seen_names.add(strategy_name)
            try:
                content = strategy_path.read_text(encoding="utf-8")
                save_strategy_record(state, strategy_name, content)
                loaded_count += 1
            except Exception as exc:
                append_system_log(state, f"failed to autoload strategy {strategy_name}: {exc}", level="WARN")

    if loaded_count:
        append_system_log(state, f"autoloaded {loaded_count} strategy YAML file(s) from {strategy_root}")


def build_strategy_execution_profile(strategy: Mapping[str, Any]) -> dict[str, Any]:
    formal_engine = _build_formal_engine_status()
    strategy_payload = strategy.get("strategy", {}) if isinstance(strategy.get("strategy"), Mapping) else {}
    template_id = str(strategy_payload.get("template_id") or "").strip()
    registered_templates = set(formal_engine["registered_templates"])
    formal_parser_error = str(
        strategy.get("formal_parser_error")
        or strategy_payload.get("formal_parser_error")
        or ""
    ).strip()

    if formal_parser_error:
        formal_supported = False
        reason = f"策略 YAML 未通过正式解析: {formal_parser_error}"
    elif not template_id:
        formal_supported = False
        reason = "策略 YAML 未声明正式模板 template_id，当前仅支持兼容预览，不是正式回测。"
    elif template_id not in registered_templates:
        formal_supported = False
        reason = f"策略模板 {template_id} 尚未注册到正式回测引擎，当前只能走兼容预览。"
    elif not formal_engine["ready"]:
        formal_supported = False
        reason = formal_engine["reason"]
    else:
        formal_supported = True
        reason = f"策略模板 {template_id} 已注册到正式引擎，且正式引擎基础条件已就绪。"

    evidence = [
        f"正式引擎已注册模板: {', '.join(formal_engine['registered_templates']) or '无'}",
        f"当前策略 template_id: {template_id or '未声明'}",
        formal_engine["reason"],
    ]
    if formal_parser_error:
        evidence.append(f"formal_parser_error: {formal_parser_error}")

    return {
        "mode": "formal" if formal_supported else "compatibility_preview",
        "label": "正式回测" if formal_supported else "兼容预览",
        "template_id": template_id or None,
        "formal_supported": formal_supported,
        "formal_parser_error": formal_parser_error or None,
        "formal_engine": formal_engine,
        "reason": reason,
        "evidence": evidence,
    }


def _build_placeholder_strategy_content(name: str) -> str:
    return "\n".join(
        [
            f'name: "{name}"',
            'description: "Service-local compatibility placeholder"',
            'template_id: "compatibility_placeholder"',
            'version: "1.0"',
            'symbols:',
            '  - "SHFE.rb2505"',
            'timeframe_minutes: 5',
            'signal:',
            '  confirm_bars: 1',
            'risk:',
            '  max_drawdown_pct: 8',
        ]
    )


def _append_history(series: list[float], value: float) -> None:
    series.append(round(value, 1))
    del series[:-METRIC_HISTORY_LIMIT]


def append_system_log(state: dict[str, Any], message: str, level: str = "INFO") -> None:
    state["system_logs"].append(f"{_clock_text(_now_ts())} [{level}] {message}")
    del state["system_logs"][:-SYSTEM_LOG_LIMIT]


def append_event_log(
    state: dict[str, Any],
    *,
    strategy: str,
    action: str,
    contract: Optional[str] = None,
    result: Optional[str] = None,
) -> None:
    state["event_logs"].insert(
        0,
        {
            "time": _clock_text(_now_ts()),
            "strategy": strategy,
            "action": action,
            "contract": contract,
            "result": result,
        },
    )
    del state["event_logs"][EVENT_LOG_LIMIT:]


def _active_result_count(state: Mapping[str, Any]) -> int:
    return sum(
        1
        for result in state.get("results", {}).values()
        if result.get("status") in ACTIVE_STATUSES
    )


def _sync_runtime_metrics(state: dict[str, Any]) -> None:
    active_results = _active_result_count(state)
    result_count = len(state["results"])
    strategy_count = len(state["strategies"])
    request_count = state["request_count"]

    cpu = min(92.0, 14.0 + active_results * 16.0 + result_count * 1.8 + (request_count % 6) * 1.1)
    memory = min(89.0, 24.0 + strategy_count * 2.0 + result_count * 2.5)
    disk = min(78.0, 36.0 + result_count * 0.7)
    latency = 12 + active_results * 9 + (request_count % 4)

    state["last_metrics"] = {
        "cpu": round(cpu, 1),
        "memory": round(memory, 1),
        "disk": round(disk, 1),
        "latency": int(latency),
    }
    _append_history(state["cpu_history"], cpu)
    _append_history(state["memory_history"], memory)


def ensure_compat_state(app: FastAPI) -> None:
    if getattr(app.state, COMPAT_STATE_ATTR, None) is not None:
        return

    state: dict[str, Any] = {
        "boot_ts": _now_ts(),
        "request_count": 0,
        "_persisted_strategies_loaded": False,
        "strategies": {},
        "results": {},
        "event_logs": [],
        "system_logs": [],
        "cpu_history": [17.0, 18.6, 19.2],
        "memory_history": [27.5, 28.1, 28.6],
        "last_metrics": {"cpu": 19.2, "memory": 28.6, "disk": 36.0, "latency": 12},
        "tqsdk_market_cache": {"fetched_at": 0, "snapshot": None, "error": ""},
        "main_contracts": list(DEFAULT_MAIN_CONTRACTS),
        "main_contract_categories": [dict(item) for item in MAIN_CONTRACT_CATEGORIES],
        "market_quotes": [
            {"symbol": "SHFE.rb2505", "price": 3568.0, "last": 3568.0, "change": 0.82, "source": "service_local"},
            {"symbol": "DCE.i2505", "price": 782.5, "last": 782.5, "change": -0.44, "source": "service_local"},
            {"symbol": "DCE.m2505", "price": 3086.0, "last": 3086.0, "change": 0.21, "source": "service_local"},
            {"symbol": "CZCE.CF605", "price": 13925.0, "last": 13925.0, "change": 1.16, "source": "service_local"},
            {"symbol": "CZCE.MA505", "price": 2481.0, "last": 2481.0, "change": -0.33, "source": "service_local"},
        ],
    }
    setattr(app.state, COMPAT_STATE_ATTR, state)

    settings = get_settings()
    append_system_log(state, f"backtest compatibility layer booted on port {settings.service_port}")
    append_system_log(state, "market and system endpoints are backed by service-local synthetic data")
    _autoload_persisted_strategies(state)


def get_compat_state(request: Request, *, touch: bool = True) -> dict[str, Any]:
    state = getattr(request.app.state, COMPAT_STATE_ATTR, None)
    if state is None:
        ensure_compat_state(request.app)
        state = getattr(request.app.state, COMPAT_STATE_ATTR)
    if touch:
        state["request_count"] += 1
        _sync_runtime_metrics(state)
    return state


def get_strategy_record(state: Mapping[str, Any], name: str) -> Optional[dict[str, Any]]:
    return state.get("strategies", {}).get(name)


def save_strategy_record(state: dict[str, Any], name: str, content: str) -> tuple[dict[str, Any], bool]:
    now = _now_ts()
    existing = state["strategies"].get(name)
    strategy_yaml_filename, metadata, formal_parser_error, scan_result = _load_strategy_record_metadata(name, content)
    record = _compose_strategy_record(
        name=name,
        content=content,
        existing=existing,
        now=now,
        strategy_yaml_filename=strategy_yaml_filename,
        metadata=metadata,
        formal_parser_error=formal_parser_error,
        scan_result=scan_result,
    )
    state["strategies"][name] = record
    return record, existing is None


def ensure_strategy_record(state: dict[str, Any], name: str) -> dict[str, Any]:
    existing = state["strategies"].get(name)
    if existing is not None:
        return existing
    record, _ = save_strategy_record(state, name, _build_placeholder_strategy_content(name))
    return record


def latest_result_for_strategy(state: Mapping[str, Any], strategy_name: str) -> Optional[dict[str, Any]]:
    for result in list_results_sorted(state):
        payload_strategy = result.get("payload", {}).get("strategy", {})
        if result.get("strategy") == strategy_name or result.get("name") == strategy_name or payload_strategy.get("id") == strategy_name:
            return result
    return None


def serialize_strategy(state: Mapping[str, Any], strategy: Mapping[str, Any]) -> dict[str, Any]:
    latest_result = latest_result_for_strategy(state, str(strategy.get("name", "")))
    status = latest_result.get("status") if latest_result is not None else strategy.get("status", "local")
    return {
        "id": strategy.get("id"),
        "name": strategy.get("name"),
        "status": status,
        "created_at": strategy.get("created_at"),
        "updated_at": strategy.get("updated_at"),
        "params": strategy.get("params", {}),
        "symbols": strategy.get("symbols", []),
        "capital_params": strategy.get("capital_params", {}),
        "signal": strategy.get("signal", {}),
        "risk": strategy.get("risk", {}),
        "strategy_yaml_filename": strategy.get("strategy_yaml_filename"),
        "strategy": strategy.get("strategy", {}),
        "scan_result": strategy.get("scan_result", {}),
        "execution_profile": build_strategy_execution_profile(strategy),
    }


def resolve_result_report_file(report_path: str) -> Path:
    settings = get_settings()
    result_root = settings.backtest_result_dir.expanduser().resolve()
    candidate = (result_root / report_path).resolve()
    if result_root not in candidate.parents:
        raise ValueError("report_path must stay within BACKTEST_RESULT_DIR")
    return candidate


def build_result_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    is_active = result.get("status") in ACTIVE_STATUSES
    summary = {
        "id": result.get("id"),
        "task_id": result.get("task_id"),
        "name": result.get("name"),
        "strategy": result.get("strategy"),
        "status": result.get("status"),
        "payload": result.get("payload", {}),
        "totalReturn": None if is_active else result.get("totalReturn"),
        "annualReturn": None if is_active else result.get("annualReturn"),
        "maxDrawdown": None if is_active else result.get("maxDrawdown"),
        "sharpeRatio": None if is_active else result.get("sharpeRatio"),
        "winRate": None if is_active else result.get("winRate"),
        "profitLossRatio": None if is_active else result.get("profitLossRatio"),
        "totalTrades": None if is_active else result.get("totalTrades"),
        "total_trades": None if is_active else result.get("total_trades"),
        "initialCapital": result.get("initialCapital"),
        "finalCapital": None if is_active else result.get("finalCapital"),
        "submitted_at": result.get("submitted_at"),
        "contracts": result.get("contracts", []),
        "error_message": result.get("error_message"),
        "result": {} if is_active else result.get("result", {}),
        "tqsdk_stat": {} if is_active else result.get("tqsdk_stat", {}),
        "source": result.get("source"),
        "report_path": result.get("report_path"),
        "execution_profile": result.get("execution_profile", {}),
        "transaction_cost_summary": result.get("transaction_cost_summary", {}),
    }
    return summary


def list_results_sorted(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        state.get("results", {}).values(),
        key=lambda item: item.get("submitted_at", 0),
        reverse=True,
    )


@router.get("/system/status")
def get_system_status(request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    elapsed = _now_ts() - state["boot_ts"]
    metrics = state["last_metrics"]
    request_count = state["request_count"]

    services = [
        {
            "id": "backtest-api",
            "name": "backtest-api",
            "status": "running",
            "uptime": _format_uptime(elapsed),
            "requests": request_count,
            "latency": metrics["latency"],
        },
        {
            "id": "compat-router",
            "name": "compat-router",
            "status": "running",
            "uptime": _format_uptime(elapsed),
            "requests": len(state["event_logs"]),
            "latency": max(6, metrics["latency"] - 3),
        },
    ]

    return {
        "cpu": metrics["cpu"],
        "memory": metrics["memory"],
        "disk": metrics["disk"],
        "latency": metrics["latency"],
        "cpuHistory": state["cpu_history"],
        "memoryHistory": state["memory_history"],
        "services": services,
        "formal_engine": _build_formal_engine_status(),
    }


@router.get("/system/logs", response_class=PlainTextResponse)
def get_system_logs(request: Request) -> PlainTextResponse:
    state = get_compat_state(request)
    return PlainTextResponse("\n".join(state["system_logs"]))


@router.get("/market/quotes")
def get_market_quotes(request: Request) -> list[dict[str, Any]]:
    state = get_compat_state(request)
    live_snapshot = _get_tqsdk_market_snapshot(state)
    if live_snapshot and live_snapshot.get("quotes"):
        return [dict(item) for item in live_snapshot["quotes"]]
    return list(state["market_quotes"])


@router.get("/market/main-contracts")
def get_main_contracts(request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    live_snapshot = _get_tqsdk_market_snapshot(state)
    if live_snapshot and live_snapshot.get("main_contracts"):
        return {
            "contracts": list(live_snapshot["main_contracts"]),
            "categories": list(state.get("main_contract_categories", [])),
            "source": str(live_snapshot.get("source") or "tqsdk_realtime_main_contracts"),
            "note": str(live_snapshot.get("note") or "TqSdk 实时主力合约清单；查询失败时会自动回退到本地兼容清单。"),
        }
    return {
        "contracts": list(state["main_contracts"]),
        "categories": list(state.get("main_contract_categories", [])),
        "source": "service_local_compatibility",
        "note": "兼容层本地主力合约清单，仅供分类选择与界面联调，不代表实时主力行情。",
    }


@router.get("/v1/factors")
def list_registered_factors() -> dict[str, Any]:
    """Return all registered factors with alias information."""
    if _factor_registry is None:
        return {"factors": [], "count": 0}
    try:
        factors = _factor_registry.list_factors_with_aliases()
    except Exception:
        factors = [{"name": n, "display_name": n, "aliases": [n]} for n in _factor_registry.list_factors()]
    return {"factors": factors, "count": len(factors)}


@router.get("/market/list")
def list_available_markets(request: Request) -> dict[str, Any]:
    return {
        "markets": [
            {
                "key": category["key"],
                "name_zh": category["zh"],
                "name_en": category["en"],
                "codes": category["codes"],
            }
            for category in MAIN_CONTRACT_CATEGORIES
        ],
        "total": len(MAIN_CONTRACT_CATEGORIES),
    }