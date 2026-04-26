#!/usr/bin/env python3
"""Normalize multi-source JSON/JSONL samples into mlx-lm friendly records."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SYSTEM_PROMPT = (
    "You are the JBT researcher model. Return strict JSON only. "
    "Do not emit reasoning, markdown fences, or think tags."
)

TEXT_CANDIDATE_PAIRS = (
    ("instruction", "input", "output"),
    ("prompt", "context", "response"),
    ("question", "context", "answer"),
    ("task", "input", "target"),
    ("instruction", "context", "answer"),
    ("prompt", "input", "completion"),
    ("prompt", "input", "output"),
    ("request", "context", "response"),
)


@dataclass
class NormalizedSample:
    instruction: str
    input_text: str
    output_text: str
    source_format: str
    source_id: str
    source_path: str
    system_prompt: str = DEFAULT_SYSTEM_PROMPT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize F4 multi-source samples into Alpaca or chat records."
    )
    parser.add_argument(
        "--input",
        dest="inputs",
        action="append",
        required=True,
        help="Input file or directory. Repeat for multiple sources.",
    )
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument(
        "--format",
        choices=("alpaca", "messages"),
        default="messages",
        help="Normalized output structure.",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="Default system prompt injected when source records do not provide one.",
    )
    parser.add_argument(
        "--keep-metadata",
        action="store_true",
        help="Preserve source metadata alongside training fields.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Optional hard cap for emitted samples. 0 means no cap.",
    )
    return parser.parse_args()


def iter_input_files(raw_inputs: Iterable[str]) -> Iterable[Path]:
    for raw_path in raw_inputs:
        path = Path(raw_path).expanduser()
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.suffix.lower() in {".json", ".jsonl"} and child.is_file():
                    yield child
        elif path.is_file():
            yield path
        else:
            raise FileNotFoundError(f"Input path not found: {path}")


def load_records(path: Path) -> Iterable[tuple[int, Any]]:
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                yield line_number, json.loads(line)
        return

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list):
        for index, item in enumerate(payload, start=1):
            yield index, item
        return

    yield 1, payload


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value).strip()


def extract_from_messages(record: dict[str, Any], source_path: str, source_id: str) -> NormalizedSample | None:
    raw_messages = record.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages:
        return None

    system_prompt = DEFAULT_SYSTEM_PROMPT
    user_parts: list[str] = []
    assistant_parts: list[str] = []

    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        content = clean_text(item.get("content", ""))
        if not content:
            continue
        if role == "system":
            system_prompt = content
        elif role == "assistant":
            assistant_parts.append(content)
        elif role in {"user", "human"}:
            user_parts.append(content)

    if not user_parts or not assistant_parts:
        return None

    return NormalizedSample(
        instruction=user_parts[0],
        input_text="\n\n".join(user_parts[1:]),
        output_text="\n\n".join(assistant_parts),
        source_format="messages",
        source_id=source_id,
        source_path=source_path,
        system_prompt=system_prompt,
    )


def extract_from_text_fields(record: dict[str, Any], source_path: str, source_id: str) -> NormalizedSample | None:
    for instruction_key, input_key, output_key in TEXT_CANDIDATE_PAIRS:
        if instruction_key not in record or output_key not in record:
            continue
        instruction = clean_text(record.get(instruction_key))
        input_text = clean_text(record.get(input_key)) if input_key in record else ""
        output_text = clean_text(record.get(output_key))
        if instruction and output_text:
            return NormalizedSample(
                instruction=instruction,
                input_text=input_text,
                output_text=output_text,
                source_format=f"fields:{instruction_key}/{input_key}/{output_key}",
                source_id=source_id,
                source_path=source_path,
            )
    return None


def extract_report_style(record: dict[str, Any], source_path: str, source_id: str) -> NormalizedSample | None:
    report_keys = [key for key in ("news_report", "futures_report", "macro_report") if key in record]
    if not report_keys:
        return None

    context = record.get("context") or record.get("input") or record.get("prompt")
    prompt = clean_text(context)
    if not prompt:
        prompt = "Summarize the provided market inputs into strict JSON with report sections."

    response_payload = {key: record[key] for key in report_keys}
    metadata = record.get("metadata")
    if isinstance(metadata, dict) and metadata:
        response_payload["metadata"] = metadata

    return NormalizedSample(
        instruction="Produce a strict JSON market research report.",
        input_text=prompt,
        output_text=json.dumps(response_payload, ensure_ascii=False, separators=(",", ":")),
        source_format="report_json",
        source_id=source_id,
        source_path=source_path,
    )


def extract_runtime_report_style(record: dict[str, Any], source_path: str, source_id: str) -> NormalizedSample | None:
    report_type = clean_text(record.get("report_type")).lower()
    data = record.get("data")
    if report_type not in {"news", "futures", "macro"} or not isinstance(data, dict) or not data:
        return None

    context_parts = [
        f"report_type={report_type}",
        f"date={clean_text(record.get('date'))}",
        f"hour={clean_text(record.get('hour'))}",
        f"model={clean_text(record.get('model'))}",
    ]
    response_payload: dict[str, Any] = {f"{report_type}_report": data}
    for extra_key in ("confidence", "symbols_covered", "data_points"):
        if extra_key in record:
            response_payload[extra_key] = record[extra_key]

    return NormalizedSample(
        instruction=f"Produce a strict JSON {report_type} research report.",
        input_text="\n".join(part for part in context_parts if part.split("=", 1)[1]),
        output_text=json.dumps(response_payload, ensure_ascii=False, separators=(",", ":")),
        source_format="runtime_report",
        source_id=source_id,
        source_path=source_path,
    )


def extract_cycle_summary_style(record: dict[str, Any], source_path: str, source_id: str) -> NormalizedSample | None:
    summary_keys = [
        key for key in ("futures_summary", "stocks_summary", "crawler_stats", "change_highlights")
        if key in record
    ]
    if not summary_keys:
        return None

    response_payload = {key: record[key] for key in summary_keys}
    if "previous_report_id" in record:
        response_payload["previous_report_id"] = record["previous_report_id"]

    context_parts = [
        f"date={clean_text(record.get('date'))}",
        f"segment={clean_text(record.get('segment'))}",
        f"generated_at={clean_text(record.get('generated_at'))}",
        f"model={clean_text(record.get('model'))}",
    ]
    return NormalizedSample(
        instruction="Produce a strict JSON cycle summary report.",
        input_text="\n".join(part for part in context_parts if part.split("=", 1)[1]),
        output_text=json.dumps(response_payload, ensure_ascii=False, separators=(",", ":")),
        source_format="cycle_summary",
        source_id=source_id,
        source_path=source_path,
    )


def extract_article_style(record: dict[str, Any], source_path: str, source_id: str) -> NormalizedSample | None:
    title = clean_text(record.get("title"))
    content = clean_text(record.get("content"))
    summary = clean_text(record.get("summary_cn"))
    if not title or not content or not summary:
        return None

    response_payload: dict[str, Any] = {
        "category": clean_text(record.get("category")) or "general",
        "relevance": record.get("relevance"),
        "sentiment": clean_text(record.get("sentiment")) or "neutral",
        "impact": clean_text(record.get("impact_level")) or "medium",
        "symbols": record.get("affected_symbols") or [],
        "summary": summary,
        "key_points": record.get("key_points") or [],
        "is_urgent": bool(record.get("is_urgent", False)),
    }
    response_payload = {
        key: value
        for key, value in response_payload.items()
        if value not in (None, "", [], {})
    }

    input_parts = [
        f"标题：{title}",
        f"正文：{content}",
    ]
    if clean_text(record.get("source_name")):
        input_parts.append(f"来源：{clean_text(record.get('source_name'))}")

    return NormalizedSample(
        instruction="Read the market news article and return strict JSON only.",
        input_text="\n".join(input_parts),
        output_text=json.dumps(response_payload, ensure_ascii=False, separators=(",", ":")),
        source_format="article_json",
        source_id=source_id or clean_text(record.get("article_id")),
        source_path=source_path,
    )


def normalize_record(record: Any, source_path: Path, line_number: int) -> NormalizedSample | None:
    if not isinstance(record, dict):
        return None

    source_id = clean_text(record.get("id") or record.get("sample_id") or f"{source_path.name}:{line_number}")
    normalized = extract_from_messages(record, str(source_path), source_id)
    if normalized is not None:
        return normalized

    normalized = extract_from_text_fields(record, str(source_path), source_id)
    if normalized is not None:
        return normalized

    normalized = extract_report_style(record, str(source_path), source_id)
    if normalized is not None:
        return normalized

    normalized = extract_runtime_report_style(record, str(source_path), source_id)
    if normalized is not None:
        return normalized

    normalized = extract_cycle_summary_style(record, str(source_path), source_id)
    if normalized is not None:
        return normalized

    normalized = extract_article_style(record, str(source_path), source_id)
    if normalized is not None:
        return normalized

    return None


def to_alpaca(sample: NormalizedSample, keep_metadata: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "instruction": sample.instruction,
        "input": sample.input_text,
        "output": sample.output_text,
    }
    if keep_metadata:
        payload["metadata"] = {
            "source_format": sample.source_format,
            "source_id": sample.source_id,
            "source_path": sample.source_path,
        }
    return payload


def to_messages(sample: NormalizedSample, keep_metadata: bool, system_prompt: str) -> dict[str, Any]:
    user_content = sample.instruction
    if sample.input_text:
        user_content = f"{sample.instruction}\n\nContext:\n{sample.input_text}"

    payload: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": sample.system_prompt or system_prompt},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": sample.output_text},
        ]
    }
    if keep_metadata:
        payload["metadata"] = {
            "source_format": sample.source_format,
            "source_id": sample.source_id,
            "source_path": sample.source_path,
        }
    return payload


def main() -> None:
    args = parse_args()
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    stats = Counter()
    normalized_records: list[dict[str, Any]] = []

    for source_file in iter_input_files(args.inputs):
        stats["files_seen"] += 1
        for line_number, raw_record in load_records(source_file):
            stats["records_seen"] += 1
            sample = normalize_record(raw_record, source_file, line_number)
            if sample is None:
                stats["records_skipped"] += 1
                continue

            stats[f"source_format:{sample.source_format}"] += 1
            if args.format == "alpaca":
                normalized_records.append(to_alpaca(sample, args.keep_metadata))
            else:
                normalized_records.append(
                    to_messages(sample, args.keep_metadata, args.system_prompt)
                )
            stats["records_emitted"] += 1

            if args.max_samples and stats["records_emitted"] >= args.max_samples:
                break
        if args.max_samples and stats["records_emitted"] >= args.max_samples:
            break

    with output_path.open("w", encoding="utf-8") as handle:
        for record in normalized_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "output": str(output_path),
        "format": args.format,
        "files_seen": stats["files_seen"],
        "records_seen": stats["records_seen"],
        "records_emitted": stats["records_emitted"],
        "records_skipped": stats["records_skipped"],
        "source_formats": {
            key.split(":", 1)[1]: value
            for key, value in stats.items()
            if key.startswith("source_format:")
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()