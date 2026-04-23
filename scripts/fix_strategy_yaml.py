#!/usr/bin/env python3
"""
Strategy YAML Import Error Fixer

修复策略 YAML 文件中的结构性/校验性问题，使其能顺利通过 import 接口。
原则：只修复会导致 422 / StrategyConfigError 的无效值，绝不改动策略本身的参数
（period / multiplier / fast / slow / signal / position_fraction / threshold 等）。

已知修复规则：
  1. signal.confirm_bars <= 0  →  1（必须为正整数，0 / 负数无意义）
  2. signal.ema_periods <= 0   →  1（同上，若存在）
  3. (扩展) factors[*].weight < 0 → abs(weight)，负权重不合法

用法：
  # 修复单文件（默认 in-place）
  python scripts/fix_strategy_yaml.py path/to/strategy.yaml

  # 修复目录下所有 .yaml
  python scripts/fix_strategy_yaml.py 参考文件/策略/

  # 仅预览，不写入（dry-run）
  python scripts/fix_strategy_yaml.py 参考文件/策略/ --dry-run

  # 修复后通过 API 重新导入到 Air backtest 服务
  python scripts/fix_strategy_yaml.py path/to/strategy.yaml --reimport --api http://192.168.31.156:8103
"""
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ── 修复规则 ──────────────────────────────────────────────────────────────────

def _fix_signal_section(signal: dict[str, Any]) -> list[str]:
    """修复 signal 字段中的无效值。返回变更说明列表（空表示无变更）。"""
    changes: list[str] = []

    # confirm_bars 必须是正整数（>= 1）
    if "confirm_bars" in signal:
        cb = signal["confirm_bars"]
        try:
            cb_int = int(cb)
        except (TypeError, ValueError):
            signal["confirm_bars"] = 1
            changes.append(f"signal.confirm_bars: {cb!r} (非整数) → 1")
        else:
            if cb_int < 1:
                signal["confirm_bars"] = 1
                changes.append(f"signal.confirm_bars: {cb_int} → 1")

    # ema_periods 必须是正整数（若存在）
    if "ema_periods" in signal:
        ep = signal["ema_periods"]
        try:
            ep_int = int(ep)
        except (TypeError, ValueError):
            signal["ema_periods"] = 1
            changes.append(f"signal.ema_periods: {ep!r} (非整数) → 1")
        else:
            if ep_int < 1:
                signal["ema_periods"] = 1
                changes.append(f"signal.ema_periods: {ep_int} → 1")

    return changes


def _fix_factors_section(factors: list[Any]) -> list[str]:
    """修复 factors 中的无效 weight（负数不合法）。"""
    changes: list[str] = []
    if not isinstance(factors, list):
        return changes
    for i, factor in enumerate(factors):
        if not isinstance(factor, dict):
            continue
        if "weight" in factor:
            w = factor["weight"]
            try:
                wf = float(w)
            except (TypeError, ValueError):
                continue
            if wf < 0:
                factor["weight"] = abs(wf)
                name = factor.get("factor_name", f"[{i}]")
                changes.append(f"factors[{name}].weight: {wf} → {abs(wf)}")
    return changes


def _fix_strategy_data(data: dict[str, Any]) -> list[str]:
    """应用所有修复规则到已解析的 YAML dict。返回所有变更说明。"""
    all_changes: list[str] = []

    signal = data.get("signal")
    if isinstance(signal, dict):
        all_changes.extend(_fix_signal_section(signal))

    factors = data.get("factors")
    if isinstance(factors, list):
        all_changes.extend(_fix_factors_section(factors))

    return all_changes


# ── 文件操作 ──────────────────────────────────────────────────────────────────

def _safe_yaml_dump(data: dict[str, Any]) -> str:
    """序列化 YAML，保留 unicode，不使用 flow 风格，不重排 key。"""
    return yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )


def fix_file(path: Path, dry_run: bool = False) -> list[str]:
    """修复单个 YAML 文件。dry_run=True 时只返回变更列表，不写入。"""
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        data = yaml.safe_load(raw)
    except Exception as exc:
        print(f"  [SKIP] {path}: 无法解析 — {exc}")
        return []

    if not isinstance(data, dict):
        print(f"  [SKIP] {path}: 不是 dict 类型 YAML")
        return []

    changes = _fix_strategy_data(data)

    if not changes:
        return []

    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            f.write(_safe_yaml_dump(data))

    return changes


def collect_yaml_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.rglob("*.yaml")) + sorted(target.rglob("*.yml"))


# ── API 重新导入 ──────────────────────────────────────────────────────────────

def reimport_strategy(path: Path, api_base: str) -> bool:
    """将修复后的 YAML 文件通过 /api/strategy/import 重新导入到 backtest 服务。"""
    name = path.stem  # 去掉 .yaml 后缀作为策略名
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception as exc:
        print(f"  [IMPORT ERROR] 读取文件失败: {exc}")
        return False

    payload = json.dumps({"name": name, "content": content}).encode("utf-8")
    url = f"{api_base.rstrip('/')}/api/strategy/import"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            result = json.loads(body)
            print(f"  [IMPORTED] {name} → id={result.get('id', '?')}, status={result.get('status', '?')}")
            return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"  [IMPORT FAIL] {name} → HTTP {exc.code}: {body[:200]}")
        return False
    except Exception as exc:
        print(f"  [IMPORT ERROR] {name}: {exc}")
        return False


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix strategy YAML import errors (structural fixes only, no param changes)"
    )
    parser.add_argument("targets", nargs="+", help="YAML 文件或目录（支持多个）")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入文件")
    parser.add_argument(
        "--reimport",
        action="store_true",
        help="修复后通过 API 重新导入（需要 --api）",
    )
    parser.add_argument(
        "--api",
        default="http://192.168.31.156:8103",
        help="backtest 服务 API 地址（默认: http://192.168.31.156:8103）",
    )
    args = parser.parse_args()

    total_files = 0
    total_fixed = 0
    total_failed_reimport = 0

    for target_str in args.targets:
        target = Path(target_str)
        if not target.exists():
            print(f"[NOT FOUND] {target}")
            continue

        files = collect_yaml_files(target)
        if not files:
            print(f"[NO YAML] {target} 下没有 .yaml/.yml 文件")
            continue

        for path in files:
            total_files += 1
            mode_label = "[DRY-RUN]" if args.dry_run else "[FIX]"
            changes = fix_file(path, dry_run=args.dry_run)
            if changes:
                total_fixed += 1
                print(f"{mode_label} {path}:")
                for change in changes:
                    print(f"    {change}")
                if args.reimport and not args.dry_run:
                    ok = reimport_strategy(path, args.api)
                    if not ok:
                        total_failed_reimport += 1
            # else: no changes, silent

    print()
    print(f"扫描: {total_files} 文件  |  修复: {total_fixed} 文件", end="")
    if args.reimport and not args.dry_run:
        print(f"  |  重新导入失败: {total_failed_reimport}", end="")
    print()
    if args.dry_run:
        print("（dry-run 模式，未写入任何文件）")


if __name__ == "__main__":
    main()
