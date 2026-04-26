#!/usr/bin/env python3
"""F4 + F5 数据合并去重，输出 train.jsonl + val.jsonl。

输入：
  --f4-jsonl    F4 normalized 输出（来自 prepare_dataset.py）
  --f5-jsonl    F5 主语料（来自 build_finance_corpus.py），不含 raw
  --extra-jsonl 可选额外 jsonl，多次指定

输出：
  <out>/train.jsonl
  <out>/val.jsonl
  <out>/merge_summary.json

预审硬约束：
  - 禁止读取 dataset_f5_raw.jsonl（合约规则自生成 raw 必须人工校验通过后才能合并）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Iterable


def load_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def dedup(records: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for rec in records:
        body = rec.get("messages") or {k: v for k, v in rec.items() if k != "metadata"}
        h = hashlib.sha1(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        result.append(rec)
    return result


def split_train_val(records: list[dict], val_ratio: float, seed: int) -> tuple[list[dict], list[dict]]:
    rnd = random.Random(seed)
    indices = list(range(len(records)))
    rnd.shuffle(indices)
    val_n = max(1, int(len(records) * val_ratio))
    val_idx = set(indices[:val_n])
    train = [records[i] for i in range(len(records)) if i not in val_idx]
    val = [records[i] for i in range(len(records)) if i in val_idx]
    return train, val


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge F4+F5 datasets.")
    p.add_argument("--f4-jsonl", required=True, help="F4 normalized JSONL.")
    p.add_argument("--f5-jsonl", required=True, help="F5 main JSONL (NOT _raw).")
    p.add_argument("--extra-jsonl", action="append", default=[], help="Optional extra JSONL files.")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--val-ratio", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    f5_path = Path(args.f5_jsonl).expanduser()
    if f5_path.name.endswith("_raw.jsonl"):
        raise SystemExit(
            f"FATAL: refusing to merge raw F5 file ({f5_path.name}). "
            "Pass dataset_f5.jsonl (post-review) only."
        )

    f4_records = list(load_jsonl(Path(args.f4_jsonl).expanduser()))
    f5_records = list(load_jsonl(f5_path))
    extra_records: list[dict] = []
    for extra in args.extra_jsonl:
        extra_records.extend(load_jsonl(Path(extra).expanduser()))

    merged = dedup(f4_records + f5_records + extra_records)
    train, val = split_train_val(merged, args.val_ratio, args.seed)

    write_jsonl(out_dir / "train.jsonl", train)
    write_jsonl(out_dir / "val.jsonl", val)

    summary = {
        "out_dir": str(out_dir),
        "f4_count": len(f4_records),
        "f5_count": len(f5_records),
        "extra_count": len(extra_records),
        "merged_dedup_count": len(merged),
        "train_count": len(train),
        "val_count": len(val),
        "val_ratio": args.val_ratio,
    }
    (out_dir / "merge_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
