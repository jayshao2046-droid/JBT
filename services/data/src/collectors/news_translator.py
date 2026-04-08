"""News title translator using DeepSeek API."""

from __future__ import annotations

import re
from typing import Any

import httpx

from services.data.src.utils.logger import get_logger

_logger = get_logger("data.collector.news_translator")


def is_chinese(text: str) -> bool:
    """Return True if the text is predominantly Chinese."""
    if not text:
        return False
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return chinese_chars / max(len(text), 1) > 0.3


def translate_title(title: str, api_key: str, base_url: str) -> str:
    """Translate a news title to Chinese via DeepSeek chat/completions.

    Returns the original title on any failure so collection is never blocked.
    """
    try:
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业翻译，请将以下新闻标题翻译成中文，只输出翻译结果",
                },
                {"role": "user", "content": title},
            ],
            "temperature": 0.1,
            "max_tokens": 256,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            translated = data["choices"][0]["message"]["content"].strip()
            if translated:
                return translated
    except Exception as exc:  # noqa: BLE001
        _logger.warning("translate_title failed: title=%s error=%s", title[:60], exc)
    return title


def enrich_record_with_translation(
    record: dict[str, Any],
    *,
    api_key: str | None,
    base_url: str,
    title_field: str = "title",
) -> dict[str, Any]:
    """Add translation fields to a single collector record's payload.

    Fields added/modified in payload:
      - title          : translated (or original if already Chinese / translation fails)
      - title_original : always the raw title
      - language        : detected source language tag
      - translated      : bool indicating whether translation was performed
    """
    payload = record.get("payload", {})
    original_title = payload.get(title_field, "")

    payload["title_original"] = original_title

    if not api_key or not original_title or is_chinese(original_title):
        payload["language"] = "zh" if is_chinese(original_title) else "unknown"
        payload["translated"] = False
        record["payload"] = payload
        return record

    translated = translate_title(original_title, api_key, base_url)
    payload["title"] = translated
    payload["translated"] = translated != original_title
    payload["language"] = "en"  # non-Chinese source
    record["payload"] = payload
    return record
