"""新闻前置筛选器（两段式管线第一段）

由 F1（2026-04-24）引入：
- 第一段：小模型 qwen2.5:7b-instruct-q4_K_M 0–10 打分（本模块）
- 第二段：14B qwen3:14b 深分析（仍由 scheduler._analyze_single_article 处理）

设计要点：
1. keep_alive 短（默认 30s），避免 7B 与 14B 同时常驻 8GB 显存。
2. 单条 timeout 10s，失败时按"放行"策略（score=阈值）走向 14B，避免误杀。
3. 通过 ResearcherConfig.OLLAMA_PREFILTER_ENABLED 一键回滚到单段式。
4. 不接触 daily_stats / queue_manager / 入库逻辑，仅做评分和过滤。
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Tuple

import httpx

from .config import ResearcherConfig
from .prompts import NEWS_PREFILTER_PROMPT

logger = logging.getLogger(__name__)


async def _score_one(client: httpx.AsyncClient, article: Dict) -> Tuple[int, str]:
    """对单条新闻调用小模型打分。失败按阈值放行。"""
    title = (article.get("title") or "").strip()
    content = (article.get("content") or article.get("summary") or "").strip()
    prompt = NEWS_PREFILTER_PROMPT.format(title=title[:120], content=content[:400])

    try:
        resp = await client.post(
            f"{ResearcherConfig.OLLAMA_URL}/api/generate",
            json={
                "model": ResearcherConfig.OLLAMA_PREFILTER_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": ResearcherConfig.OLLAMA_PREFILTER_KEEP_ALIVE,
                "options": {
                    "temperature": 0.0,
                    "num_ctx": 2048,
                    "num_predict": 64,
                },
            },
            timeout=ResearcherConfig.OLLAMA_PREFILTER_TIMEOUT,
        )
        if resp.status_code != 200:
            return ResearcherConfig.OLLAMA_PREFILTER_THRESHOLD, f"http_{resp.status_code}_passthrough"
        text = (resp.json().get("response") or "").strip()
        # 移除可能的 <think> 块
        if "<think>" in text and "</think>" in text:
            text = text[text.index("</think>") + len("</think>"):].strip()
        if "{" in text and "}" in text:
            json_str = text[text.index("{"):text.rindex("}") + 1]
            obj = json.loads(json_str)
            score = int(obj.get("score", ResearcherConfig.OLLAMA_PREFILTER_THRESHOLD))
            score = max(0, min(10, score))
            reason = str(obj.get("reason", ""))[:40]
            return score, reason
        return ResearcherConfig.OLLAMA_PREFILTER_THRESHOLD, "no_json_passthrough"
    except Exception as exc:
        logger.debug("[PREFILTER] 调用异常（按放行处理）: %s", exc)
        return ResearcherConfig.OLLAMA_PREFILTER_THRESHOLD, "exc_passthrough"


async def _unload_prefilter_model() -> None:
    """显式让 7B 卸载，给 14B 让出显存。"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{ResearcherConfig.OLLAMA_URL}/api/generate",
                json={
                    "model": ResearcherConfig.OLLAMA_PREFILTER_MODEL,
                    "prompt": "",
                    "stream": False,
                    "keep_alive": 0,
                },
            )
    except Exception as exc:
        logger.debug("[PREFILTER] 卸载小模型失败（忽略）: %s", exc)


async def prefilter_news(articles: List[Dict]) -> List[Dict]:
    """对一批新闻执行前置筛选，返回 score >= 阈值的子集。

    每篇文章会被附加 ``_prefilter_score`` 与 ``_prefilter_reason`` 字段，
    以便下游日志/调试。

    若 ``OLLAMA_PREFILTER_ENABLED=false``，原样透传。
    """
    if not ResearcherConfig.OLLAMA_PREFILTER_ENABLED:
        for art in articles:
            art["_prefilter_score"] = 10
            art["_prefilter_reason"] = "disabled"
        return articles

    if not articles:
        return articles

    threshold = ResearcherConfig.OLLAMA_PREFILTER_THRESHOLD
    kept: List[Dict] = []
    t0 = time.time()
    async with httpx.AsyncClient(timeout=ResearcherConfig.OLLAMA_PREFILTER_TIMEOUT + 5) as client:
        for art in articles:
            score, reason = await _score_one(client, art)
            art["_prefilter_score"] = score
            art["_prefilter_reason"] = reason
            if score >= threshold:
                kept.append(art)
    elapsed = time.time() - t0

    logger.info(
        "[PREFILTER] 输入 %d 条 → 通过 %d 条（阈值=%d，模型=%s，耗时=%.1fs）",
        len(articles), len(kept), threshold,
        ResearcherConfig.OLLAMA_PREFILTER_MODEL, elapsed,
    )

    # 错峰：让 7B 卸载，给 14B 腾显存
    await _unload_prefilter_model()
    return kept
