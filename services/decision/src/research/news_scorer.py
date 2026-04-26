"""盘前资讯打分模块 — TASK-0117 模块 3

读取 qwen3 研报 → 调 qwen3 对每条资讯打标：
- 影响品种列表（从 35 品种中圈定）
- 紧急程度评分（0-10）
已持有品种相关资讯若评分 > 7 → 飞书 blue 推送
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from .research_store import ResearchStore

logger = logging.getLogger(__name__)


class NewsScorer:
    """读取 qwen3 研报 → 调 qwen3 对每条资讯打标。

    已持有品种相关资讯若评分 > 7 → 飞书 blue 推送
    """

    SCORE_THRESHOLD = 7         # 推送阈值
    OLLAMA_MODEL = "qwen3:14b-q4_K_M"
    OLLAMA_TIMEOUT = 10.0       # qwen3 超时 10s

    # 35 品种白名单
    SYMBOLS_WHITELIST = {
        "rb", "hc", "i", "j", "jm", "cu", "al", "zn", "ni", "ss",
        "au", "ag", "sc", "fu", "bu", "ru", "sp", "ap", "cf", "sr",
        "ma", "ta", "eg", "pp", "l", "v", "eb", "pg", "lh", "p",
        "y", "a", "c", "cs", "m",
    }

    def __init__(
        self,
        data_api_url: Optional[str] = None,
        ollama_url: Optional[str] = None,
    ):
        """初始化资讯打分器。

        Args:
            data_api_url: 数据服务 API 地址（保留兼容，当前未使用）
            ollama_url: Ollama API 地址
        """
        self.ollama_url = ollama_url or os.getenv(
            "OLLAMA_BASE_URL", "http://192.168.31.142:11434"
        )

    async def score_report(
        self, held_symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """读取研报并对每条资讯打分。

        Args:
            held_symbols: 当前持有品种列表

        Returns:
            [{"title": ..., "symbols": [...], "score": 8, "pushed": True}, ...]
        """
        # 拉取最新研报
        report = await self._fetch_latest_report()
        if not report:
            logger.warning("研报为空，跳过打分")
            return []

        # 提取资讯列表
        news_items = self._extract_news_items(report)
        if not news_items:
            logger.info("研报中无资讯条目")
            return []

        logger.info(f"研报包含 {len(news_items)} 条资讯，开始打分")

        results = []
        for item in news_items:
            # 调用 qwen3 打分
            score_result = await self._score_single_item(item)

            if score_result is None:
                continue

            # 过滤幻觉品种（不在 35 品种白名单中）
            valid_symbols = [
                s for s in score_result["symbols"]
                if s in self.SYMBOLS_WHITELIST
            ]

            result = {
                "title": item.get("title", "无标题"),
                "symbols": valid_symbols,
                "score": score_result["urgency"],
                "reason": score_result.get("reason", ""),
                "pushed": False,
            }

            # 判断是否需要推送
            if self._should_push(valid_symbols, held_symbols, score_result["urgency"]):
                await self._push_to_feishu(result)
                result["pushed"] = True

            results.append(result)

        return results

    async def _fetch_latest_report(self) -> Optional[Dict[str, Any]]:
        """拉取最新研报（从 Decision 本地 ResearchStore sentiment facts 聚合）。

        Returns:
            研报 JSON，失败时返回 None
        """
        try:
            snapshot = ResearchStore().get_fact_group_snapshot("sentiment", limit=10)
            if not snapshot.get("available"):
                return None

            latest = snapshot.get("latest_primary") or snapshot.get("latest") or {}
            source_report = latest.get("source_report")
            if not isinstance(source_report, dict):
                source_report = {}

            news_items = self._collect_local_news_items(snapshot)
            if not news_items:
                return None

            report = dict(source_report)
            report["news"] = news_items
            report.setdefault("report_id", latest.get("report_id") or source_report.get("report_id"))

            fact_record = latest.get("fact_record")
            if isinstance(fact_record, dict):
                generated_at = fact_record.get("generated_at")
                if generated_at:
                    report.setdefault("generated_at", generated_at)

            return report

        except Exception as e:
            logger.warning(f"拉取研报失败: {e}", exc_info=True)
            return None

    @staticmethod
    def _news_items_from_report(report: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not isinstance(report, dict):
            return []

        if isinstance(report.get("news"), list):
            return report["news"]

        if isinstance(report.get("news_items"), list):
            return report["news_items"]

        crawler_stats = report.get("crawler_stats")
        if isinstance(crawler_stats, dict) and isinstance(crawler_stats.get("news_items"), list):
            return crawler_stats["news_items"]

        summary = report.get("summary") or report.get("content")
        title = report.get("title") or report.get("report_id")
        if summary or title:
            return [{
                "title": title or "研报摘要",
                "content": summary or "",
                "source": report.get("source", "research_store"),
            }]

        return []

    def _collect_local_news_items(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        history = snapshot.get("history") or []
        collected: List[Dict[str, Any]] = []
        seen: set[str] = set()

        for record in history:
            if not isinstance(record, dict):
                continue

            source_report = record.get("source_report")
            if not isinstance(source_report, dict):
                continue

            for item in self._news_items_from_report(source_report):
                if not isinstance(item, dict):
                    continue

                title = str(item.get("title", "")).strip()
                content = str(item.get("content", "")).strip()
                dedup_key = f"{title}|{content[:80]}"
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                collected.append(item)

        return collected

    def _extract_news_items(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从研报中提取资讯条目列表。

        Args:
            report: 研报 JSON

        Returns:
            资讯条目列表
        """
        news_items = self._news_items_from_report(report)

        if not isinstance(news_items, list):
            logger.warning("研报 news 字段格式错误")
            return []

        return news_items

    async def _score_single_item(
        self, news_item: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """调用 qwen3 对单条资讯打分。

        Args:
            news_item: 资讯条目

        Returns:
            {"symbols": [...], "urgency": 0-10, "reason": "..."}
            解析失败或超时时返回 None
        """
        prompt = self._build_scoring_prompt(news_item)

        try:
            async with httpx.AsyncClient(timeout=self.OLLAMA_TIMEOUT) as client:
                url = f"{self.ollama_url}/api/generate"
                payload = {
                    "model": self.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1},
                }

                resp = await client.post(url, json=payload)
                resp.raise_for_status()

                data = resp.json()
                response_text = data.get("response", "")

                # 解析 JSON 输出
                result = self._parse_scoring_response(response_text)
                return result

        except httpx.TimeoutException:
            logger.warning(f"qwen3 超时: {news_item.get('title', 'N/A')}")
            return None
        except Exception as e:
            logger.warning(
                f"qwen3 调用失败: {e}",
                exc_info=True
            )
            return None

    def _build_scoring_prompt(self, news_item: Dict[str, Any]) -> str:
        """构造 qwen3 打分 prompt。

        要求输出 JSON: {"symbols": [...], "urgency": 0-10, "reason": "..."}

        Args:
            news_item: 资讯条目

        Returns:
            prompt 字符串
        """
        title = news_item.get("title", "")
        content = news_item.get("content", "")

        prompt = f"""你是期货市场分析专家。请分析以下资讯，输出 JSON 格式：

资讯标题：{title}
资讯内容：{content}

请输出以下 JSON 格式（不要有其他文字）：
{{
  "symbols": ["品种代码1", "品种代码2", ...],
  "urgency": 紧急程度评分(0-10整数),
  "reason": "评分理由"
}}

品种代码必须从以下 35 个品种中选择：
rb, hc, i, j, jm, cu, al, zn, ni, ss, au, ag, sc, fu, bu, ru, sp, ap, cf, sr, ma, ta, eg, pp, l, v, eb, pg, lh, p, y, a, c, cs, m

紧急程度评分标准：
- 0-3: 一般性资讯，影响较小
- 4-6: 中等影响，需关注
- 7-8: 重要资讯，可能影响交易决策
- 9-10: 紧急重大资讯，需立即关注

JSON:"""

        return prompt

    def _parse_scoring_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """解析 qwen3 返回的 JSON。

        Args:
            response_text: qwen3 返回文本

        Returns:
            解析后的字典，失败时返回 None
        """
        try:
            # 尝试直接解析
            result = json.loads(response_text)

            # 验证必需字段
            if "symbols" not in result or "urgency" not in result:
                logger.warning("qwen3 返回缺少必需字段")
                return None

            # 验证类型
            if not isinstance(result["symbols"], list):
                logger.warning("symbols 字段不是列表")
                return None

            if not isinstance(result["urgency"], (int, float)):
                logger.warning("urgency 字段不是数字")
                return None

            # 限制 urgency 范围
            result["urgency"] = max(0, min(10, int(result["urgency"])))

            return result

        except json.JSONDecodeError:
            # 尝试提取 JSON 片段
            try:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_text = response_text[start:end]
                    result = json.loads(json_text)
                    return result
            except Exception:
                pass

            logger.warning(f"无法解析 qwen3 返回: {response_text[:100]}")
            return None

    def _should_push(
        self,
        symbols: List[str],
        held_symbols: List[str],
        urgency: int,
    ) -> bool:
        """判断是否需要飞书推送。

        Args:
            symbols: 资讯影响的品种列表
            held_symbols: 当前持有品种列表
            urgency: 紧急程度评分

        Returns:
            是否需要推送
        """
        # 评分 > 7 且影响已持有品种
        if urgency <= self.SCORE_THRESHOLD:
            return False

        # 检查是否有交集
        held_set = set(held_symbols)
        symbols_set = set(symbols)

        return bool(held_set & symbols_set)

    async def _push_to_feishu(self, news_result: Dict[str, Any]) -> None:
        """使用 DecisionFeishuNotifier 发送 blue 📈 消息。

        Args:
            news_result: 资讯打分结果
        """
        from ..notifier.feishu import DecisionFeishuNotifier

        try:
            notifier = DecisionFeishuNotifier()

            content = (
                f"标题: {news_result['title']}\n"
                f"影响品种: {', '.join(news_result['symbols'])}\n"
                f"紧急程度: {news_result['score']}/10\n"
                f"理由: {news_result.get('reason', 'N/A')}"
            )

            await notifier.send(
                title="盘前资讯推送",
                content=content,
                level="info",
                template="blue",
            )

            logger.info(f"已推送资讯: {news_result['title']}")

        except Exception as e:
            logger.warning(f"飞书推送失败: {e}", exc_info=True)
