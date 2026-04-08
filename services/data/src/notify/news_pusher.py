"""JBT 数据端新闻清洗 + 去重 + 推送管理。

职责：
1. 3 分钟采集周期内 news_api + rss 混合采集结果接收
2. 清洗：去空标题、去 HTML 标签、标准化字段
3. 去重：基于 title+url+source 的 SHA1 持久化去重
4. 30 分钟批量推送：分 "重大新闻" / "行业新闻" 两张卡
5. 黑天鹅即时推送：关键词命中立即推送（不等 30min）
6. 底部统计：采集总量 / 清洗后 / 推送数 / 去重缓存
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CN_TZ = timezone(timedelta(hours=8))

# ── 黑天鹅关键词（即时推送触发）──────────────────────────
BLACK_SWAN_KEYWORDS_ZH = [
    "战争", "军事冲突", "武装冲突", "空袭", "导弹",
    "地震", "台风", "海啸", "洪水", "火山",
    "疫情", "紧急卫生事件", "大流行",
    "央行紧急", "紧急会议",
    "制裁", "禁运", "贸易战",
    "核", "恐袭", "恐怖袭击",
    "金融危机", "系统崩溃", "熔断",
    "暴跌", "暴涨", "崩盘",
    "总统", "主席", "总理",
    "黑天鹅",
]

BLACK_SWAN_KEYWORDS_EN = [
    "war", "military conflict", "airstrike", "missile",
    "earthquake", "tsunami", "typhoon", "hurricane",
    "pandemic", "health emergency",
    "emergency meeting", "sanctions", "embargo",
    "nuclear", "terrorist", "terrorism",
    "financial crisis", "market crash", "circuit breaker",
    "black swan", "plunge", "surge",
]

# ── 行业/市场关键词（推送过滤）──────────────────────────
MARKET_KEYWORDS = [
    "期货", "螺纹", "铁矿", "焦炭", "焦煤", "铜", "铝", "锌", "镍",
    "黄金", "白银", "原油", "天然气", "棕榈油", "豆粕", "玉米",
    "A股", "沪指", "深指", "创业板", "科创板", "北交所",
    "美联储", "加息", "降息", "LPR", "MLF", "国债",
    "GDP", "CPI", "PPI", "PMI", "非农",
    "石油", "OPEC", "沙特", "俄罗斯",
    "halt", "futures", "crude", "gold", "copper",
]

# ── 源名称中文映射 ──────────────────────────────────────
SOURCE_CN_MAP: dict[str, str] = {
    "eastmoney": "东方财富",
    "cls": "财联社",
    "sina_finance": "新浪财经",
    "jin10": "金十数据",
    "stcn": "证券时报",
    "shmet": "上海金属网",
    "rss": "RSS聚合",
    "reuters": "路透社",
    "bloomberg": "彭博社",
    "xinhua": "新华社",
    "caixin": "财新",
    "yicai": "第一财经",
    "hexun": "和讯",
    "wallstreetcn": "华尔街见闻",
    "gelonghui": "格隆汇",
}

# ── 去重持久化文件 ──────────────────────────────────────
_DEFAULT_DEDUP_FILE = Path("/runtime/data/news_dedup_uids.json")
_MAX_DEDUP_SIZE = 50000  # 最大缓存条数


def _clean_html(text: str) -> str:
    """去除 HTML 标签。"""
    return re.sub(r"<[^>]+>", "", text).strip()


def _dedup_key(title: str, url: str, source: str) -> str:
    raw = f"{title.strip()}|{url.strip()}|{source.strip()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _is_black_swan(title: str, summary: str = "") -> str | None:
    """检测黑天鹅关键词。返回命中的关键词或 None。"""
    text = f"{title} {summary}".lower()
    for kw in BLACK_SWAN_KEYWORDS_ZH:
        if kw in text:
            return kw
    for kw in BLACK_SWAN_KEYWORDS_EN:
        if kw in text:
            return kw
    return None


def _is_market_related(title: str, url: str = "") -> bool:
    """判断是否市场/行业相关新闻。"""
    text = f"{title} {url}".lower()
    return any(kw.lower() in text for kw in MARKET_KEYWORDS)


class NewsPusher:
    """新闻清洗 + 去重 + 批量推送管理器。"""

    BATCH_INTERVAL_SEC = 1800  # 30 分钟

    def __init__(
        self,
        *,
        dedup_file: Path | None = None,
    ) -> None:
        self._dedup_file = dedup_file or _DEFAULT_DEDUP_FILE
        self._dedup_uids: set[str] = set()
        self._push_buffer: list[dict[str, Any]] = []
        self._last_push_ts: float = time.time()

        # 统计
        self._total_collected = 0
        self._total_cleaned = 0
        self._total_pushed = 0

        self._load_dedup_cache()

    def _load_dedup_cache(self) -> None:
        if self._dedup_file.exists():
            try:
                data = json.loads(self._dedup_file.read_text(encoding="utf-8"))
                self._dedup_uids = set(data.get("uids", []))
                logger.info("loaded %d dedup uids from %s", len(self._dedup_uids), self._dedup_file)
            except Exception as exc:
                logger.warning("dedup cache load failed: %s", exc)

    def _save_dedup_cache(self) -> None:
        try:
            self._dedup_file.parent.mkdir(parents=True, exist_ok=True)
            # 保留最近的条目
            uids = list(self._dedup_uids)
            if len(uids) > _MAX_DEDUP_SIZE:
                uids = uids[-_MAX_DEDUP_SIZE:]
                self._dedup_uids = set(uids)
            self._dedup_file.write_text(
                json.dumps({"uids": uids, "updated": datetime.now(CN_TZ).isoformat()}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("dedup cache save failed: %s", exc)

    def ingest(self, raw_records: list[dict[str, Any]]) -> dict[str, Any]:
        """接收原始采集结果，清洗 + 去重 + 分类。

        Returns stats: {"collected": int, "cleaned": int, "new": int, "breaking": list}
        """
        self._total_collected += len(raw_records)
        cleaned: list[dict[str, Any]] = []
        breaking: list[dict[str, Any]] = []

        for record in raw_records:
            title = _clean_html(str(record.get("title") or record.get("title_zh") or ""))
            if not title or len(title) < 4:
                continue

            url = str(record.get("url") or record.get("link") or "")
            source = str(record.get("source") or record.get("provider") or record.get("feed") or "")
            summary = _clean_html(str(record.get("summary") or record.get("summary_zh") or ""))
            source_cn = SOURCE_CN_MAP.get(source, source)

            uid = _dedup_key(title, url, source)
            if uid in self._dedup_uids:
                continue
            self._dedup_uids.add(uid)

            item = {
                "title": title,
                "url": url,
                "source": source,
                "source_cn": source_cn,
                "summary": summary,
                "uid": uid,
                "timestamp": record.get("timestamp") or datetime.now(CN_TZ).isoformat(),
            }

            # 黑天鹅检测
            kw_hit = _is_black_swan(title, summary)
            if kw_hit:
                item["breaking"] = True
                item["keyword_hit"] = kw_hit
                breaking.append(item)
            elif _is_market_related(title, url):
                item["market_related"] = True

            cleaned.append(item)

        self._total_cleaned += len(cleaned)
        self._push_buffer.extend(cleaned)
        self._save_dedup_cache()

        return {
            "collected": len(raw_records),
            "cleaned": len(cleaned),
            "new": len(cleaned),
            "breaking": breaking,
        }

    def should_push_batch(self) -> bool:
        """是否到了 30 分钟批量推送时间。"""
        return (time.time() - self._last_push_ts) >= self.BATCH_INTERVAL_SEC

    def get_batch_items(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """获取待推送的重大新闻和行业新闻。

        Returns: (major_items, industry_items)
        """
        major: list[dict[str, Any]] = []
        industry: list[dict[str, Any]] = []

        for item in self._push_buffer:
            if item.get("breaking"):
                continue  # 黑天鹅已即时推送，不重复
            if item.get("market_related"):
                industry.append(item)
            else:
                major.append(item)

        return major, industry

    def flush_batch(self) -> None:
        """清空推送缓冲区并更新计数。"""
        self._total_pushed += len(self._push_buffer)
        self._push_buffer.clear()
        self._last_push_ts = time.time()

    @property
    def stats(self) -> dict[str, int]:
        return {
            "total_collected": self._total_collected,
            "total_cleaned": self._total_cleaned,
            "total_pushed": self._total_pushed,
            "dedup_cache_size": len(self._dedup_uids),
            "buffer_size": len(self._push_buffer),
        }
