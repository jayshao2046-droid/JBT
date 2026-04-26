#!/usr/bin/env python3
"""F5 金融领域 holdout 100 题自动评测。

输入：
  --holdout    finance_holdout_100.jsonl（每行一道题，含 expected_keys 和 expected_values）
  --model      ollama 模型名称，如 qwen3-jbt-news:14b-q4_K_M
  --ollama-host http://127.0.0.1:11434

评测维度：
  1. JSON 解析成功率
  2. 期望字段命中率（expected_keys 全部出现）
  3. 关键值匹配（expected_values 任一关键词出现在 JSON 字符串里）
  4. think 链漏出（输出含 <think> / "Let me think"）

输出：
  <out>/eval_report.json
  <out>/eval_report.md（人类可读）
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

THINK_PATTERN = re.compile(r"<think|let me think|让我想|首先[让我]?分析", re.IGNORECASE)


def call_ollama(host: str, model: str, prompt: str, timeout: float = 120.0) -> tuple[str, float]:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 1024},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    dt = time.time() - t0
    obj = json.loads(body)
    return obj.get("response", ""), dt


def try_parse_json(text: str) -> dict | None:
    """Robust JSON extract: strip markdown fences and locate the first {...} block."""
    text = text.strip()
    text = re.sub(r"```(?:json)?", "", text).strip("` \n")
    # Try direct first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Locate first balanced object
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def evaluate_one(item: dict, response: str) -> dict:
    expected_keys = item.get("expected_keys") or []
    expected_values = item.get("expected_values") or []

    parsed = try_parse_json(response)
    json_ok = parsed is not None
    text_for_match = json.dumps(parsed, ensure_ascii=False) if parsed else response

    keys_hit = 0
    if json_ok and isinstance(parsed, dict):
        for k in expected_keys:
            if k in parsed:
                keys_hit += 1
    keys_score = keys_hit / max(1, len(expected_keys)) if expected_keys else 1.0

    values_hit = 0
    for v in expected_values:
        if v.lower() in text_for_match.lower():
            values_hit += 1
    values_score = values_hit / max(1, len(expected_values)) if expected_values else 1.0

    think_leak = bool(THINK_PATTERN.search(response))

    # 综合通过判定：JSON 解析成功 + 字段命中率 ≥ 0.6 + 关键值命中率 ≥ 0.5 + 无 think 链漏出
    passed = json_ok and keys_score >= 0.6 and values_score >= 0.5 and not think_leak

    return {
        "id": item.get("id"),
        "topic": item.get("topic"),
        "json_ok": json_ok,
        "keys_score": round(keys_score, 3),
        "values_score": round(values_score, 3),
        "think_leak": think_leak,
        "passed": passed,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="F5 finance holdout evaluator.")
    p.add_argument("--holdout", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--ollama-host", default="http://127.0.0.1:11434")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--timeout", type=float, default=120.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    holdout_path = Path(args.holdout).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    items: list[dict] = []
    with holdout_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    if args.limit:
        items = items[: args.limit]

    results: list[dict] = []
    total_latency = 0.0
    for idx, item in enumerate(items, 1):
        prompt = item["prompt"]
        try:
            response, dt = call_ollama(args.ollama_host, args.model, prompt, timeout=args.timeout)
        except (urllib.error.URLError, TimeoutError) as e:
            results.append({
                "id": item.get("id"),
                "topic": item.get("topic"),
                "json_ok": False,
                "keys_score": 0.0,
                "values_score": 0.0,
                "think_leak": False,
                "passed": False,
                "error": str(e),
            })
            continue
        total_latency += dt
        result = evaluate_one(item, response)
        result["latency_s"] = round(dt, 2)
        results.append(result)
        if idx % 10 == 0:
            print(f"[{idx}/{len(items)}] passed={sum(r['passed'] for r in results)}", flush=True)

    n = len(results)
    passed = sum(1 for r in results if r["passed"])
    json_ok = sum(1 for r in results if r["json_ok"])
    avg_keys = sum(r["keys_score"] for r in results) / max(1, n)
    avg_values = sum(r["values_score"] for r in results) / max(1, n)
    think_leak_rate = sum(1 for r in results if r["think_leak"]) / max(1, n)
    avg_latency = total_latency / max(1, n)

    summary = {
        "model": args.model,
        "holdout": str(holdout_path),
        "n": n,
        "passed": passed,
        "pass_rate": round(passed / max(1, n), 3),
        "json_parse_rate": round(json_ok / max(1, n), 3),
        "avg_keys_score": round(avg_keys, 3),
        "avg_values_score": round(avg_values, 3),
        "think_leak_rate": round(think_leak_rate, 3),
        "avg_latency_s": round(avg_latency, 2),
    }

    (out_dir / "eval_report.json").write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_lines = [
        f"# F5 金融 holdout 评测报告",
        "",
        f"- 模型：`{args.model}`",
        f"- 总题数：{n}",
        f"- **综合通过率：{summary['pass_rate']*100:.1f}%**（验收阈 ≥ 80%）",
        f"- JSON 解析成功率：{summary['json_parse_rate']*100:.1f}%（验收阈 ≥ 99%）",
        f"- 平均字段命中：{summary['avg_keys_score']*100:.1f}%",
        f"- 平均关键值命中：{summary['avg_values_score']*100:.1f}%",
        f"- think 链漏出率：{summary['think_leak_rate']*100:.2f}%（验收阈 ≤ 1%）",
        f"- 平均推理延迟：{summary['avg_latency_s']}s",
        "",
        "## 失败明细",
        "",
    ]
    for r in results:
        if not r["passed"]:
            md_lines.append(
                f"- [{r.get('id')}] {r.get('topic')} | json={r['json_ok']} keys={r['keys_score']} "
                f"values={r['values_score']} think={r['think_leak']} err={r.get('error', '')}"
            )
    (out_dir / "eval_report.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
