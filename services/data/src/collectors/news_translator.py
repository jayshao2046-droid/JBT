"""News title translator — DEPRECATED (TASK-0031: removed DeepSeek translation).

All functions are no-ops that return the original data unchanged.
Kept as stubs to avoid ImportError in any leftover callers.
"""

from __future__ import annotations

from typing import Any


def is_chinese(text: str) -> bool:
    """Return True if the text is predominantly Chinese."""
    import re
    if not text:
        return False
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return chinese_chars / max(len(text), 1) > 0.3


def translate_title(title: str, api_key: str, base_url: str) -> str:
    """[DEPRECATED] Returns original title unchanged."""
    return title


def enrich_record_with_translation(
    record: dict[str, Any],
    *,
    api_key: str | None,
    base_url: str,
    title_field: str = "title",
) -> dict[str, Any]:
    """[DEPRECATED] Returns record unchanged."""
    return record
