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
import threading
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
    DEFAULT_STORAGE_SOURCES = (
        ("news_api", "news_api"),
        ("rss", "news_rss"),
    )

    def __init__(
        self,
        *,
        dedup_file: Path | None = None,
    ) -> None:
        self._dedup_file = dedup_file or _DEFAULT_DEDUP_FILE
        self._dispatched_uids: set[str] = set()
        self._pending_uids: set[str] = set()
        self._push_buffer: list[dict[str, Any]] = []
        self._last_push_ts: float = time.time()
        self._lock = threading.Lock()

        # 统计
        self._total_collected = 0
        self._total_cleaned = 0
        self._total_pushed = 0

        self._load_dedup_cache()

    def _load_dedup_cache(self) -> None:
        if self._dedup_file.exists():
            try:
                data = json.loads(self._dedup_file.read_text(encoding="utf-8"))
                self._dispatched_uids = set(data.get("uids", []))
                logger.info("loaded %d dedup uids from %s", len(self._dispatched_uids), self._dedup_file)
            except Exception as exc:
                logger.warning("dedup cache load failed: %s", exc)

    def _save_dedup_cache(self) -> None:
        try:
            self._dedup_file.parent.mkdir(parents=True, exist_ok=True)
            # 保留最近的条目
            uids = list(self._dispatched_uids)
            if len(uids) > _MAX_DEDUP_SIZE:
                uids = uids[-_MAX_DEDUP_SIZE:]
                self._dispatched_uids = set(uids)
            self._dedup_file.write_text(
                json.dumps({"uids": uids, "updated": datetime.now(CN_TZ).isoformat()}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("dedup cache save failed: %s", exc)

    @staticmethod
    def _normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else None
        source_name = str(record.get("source") or record.get("symbol_or_indicator") or "")
        if payload is not None:
            source_name = str(payload.get("source") or payload.get("provider") or payload.get("feed") or source_name)
            return {
                "title": payload.get("title") or payload.get("title_zh") or "",
                "url": payload.get("url") or payload.get("link") or "",
                "summary": payload.get("summary") or payload.get("summary_zh") or payload.get("content") or payload.get("full_text") or "",
                "source": source_name,
                "timestamp": record.get("timestamp") or payload.get("time") or datetime.now(CN_TZ).isoformat(),
                "uid": payload.get("uid") or record.get("uid") or "",
            }
        if not isinstance(record, dict):
            return None
        return {
            "title": record.get("title") or record.get("title_zh") or "",
            "url": record.get("url") or record.get("link") or "",
            "summary": record.get("summary") or record.get("summary_zh") or record.get("content") or record.get("full_text") or "",
            "source": source_name,
            "timestamp": record.get("timestamp") or datetime.now(CN_TZ).isoformat(),
            "uid": record.get("uid") or "",
        }

    def sync_from_storage(
        self,
        *,
        storage: Any | None = None,
        sources: list[tuple[str, str]] | tuple[tuple[str, str], ...] | None = None,
        limit_per_source: int = 120,
    ) -> dict[str, Any]:
        """从现有 news_api/rss 存储中同步新增新闻到批量缓冲。"""
        if storage is None:
            from services.data.src.data.storage import HDF5Storage

            storage = HDF5Storage()

        raw_records: list[dict[str, Any]] = []
        for data_type, symbol in sources or self.DEFAULT_STORAGE_SOURCES:
            try:
                rows = storage.read_records(
                    data_type=data_type,
                    symbol=symbol,
                    sort_by="timestamp",
                    ascending=False,
                    limit=limit_per_source,
                )
                raw_records.extend(reversed(rows))
            except Exception as exc:
                logger.warning("news storage sync failed for %s/%s: %s", data_type, symbol, exc)

        if not raw_records:
            return {"collected": 0, "cleaned": 0, "new": 0, "breaking": []}
        return self.ingest(raw_records)

    def ingest(self, raw_records: list[dict[str, Any]]) -> dict[str, Any]:
        """接收原始采集结果，清洗 + 去重 + 分类。

        Returns stats: {"collected": int, "cleaned": int, "new": int, "breaking": list}
        """
        cleaned: list[dict[str, Any]] = []
        breaking: list[dict[str, Any]] = []

        with self._lock:
            self._total_collected += len(raw_records)

            for record in raw_records:
                normalized = self._normalize_record(record)
                if normalized is None:
                    continue

                title = _clean_html(str(normalized.get("title") or ""))
                if not title or len(title) < 4:
                    continue

                url = str(normalized.get("url") or "")
                source = str(normalized.get("source") or "")
                summary = _clean_html(str(normalized.get("summary") or ""))
                source_cn = SOURCE_CN_MAP.get(source, source)

                uid = str(normalized.get("uid") or "") or _dedup_key(title, url, source)
                if uid in self._dispatched_uids or uid in self._pending_uids:
                    continue

                item = {
                    "title": title,
                    "url": url,
                    "source": source,
                    "source_cn": source_cn,
                    "summary": summary,
                    "uid": uid,
                    "timestamp": normalized.get("timestamp") or datetime.now(CN_TZ).isoformat(),
                }

                kw_hit = _is_black_swan(title, summary)
                if kw_hit:
                    item["breaking"] = True
                    item["keyword_hit"] = kw_hit
                    breaking.append(dict(item))
                elif _is_market_related(title, url):
                    item["market_related"] = True

                self._pending_uids.add(uid)
                self._push_buffer.append(item)
                cleaned.append(item)

            self._total_cleaned += len(cleaned)

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

    def _mark_as_dispatched(self, items: list[dict[str, Any]]) -> int:
        if not items:
            return 0

        item_uids = {item.get("uid", "") for item in items}
        item_uids.discard("")
        dispatched = 0

        with self._lock:
            remaining: list[dict[str, Any]] = []
            for item in self._push_buffer:
                uid = str(item.get("uid") or "")
                if uid and uid in item_uids:
                    self._pending_uids.discard(uid)
                    self._dispatched_uids.add(uid)
                    dispatched += 1
                    continue
                remaining.append(item)

            self._push_buffer = remaining
            self._total_pushed += dispatched
            self._last_push_ts = time.time()
            self._save_dedup_cache()

        return dispatched

    @staticmethod
    def _build_breaking_body(item: dict[str, Any]) -> str:
        lines = []
        title = item.get("title", "")
        url = item.get("url", "")
        if url:
            lines.append(f"**标题:** [{title}]({url})")
        else:
            lines.append(f"**标题:** {title}")
        if item.get("source_cn"):
            lines.append(f"**来源:** {item['source_cn']}")
        if item.get("keyword_hit"):
            lines.append(f"**关键词命中:** {item['keyword_hit']}")
        if item.get("summary"):
            lines.append(f"**摘要:** {str(item['summary'])[:300]}")
        return "\n".join(lines)

    def dispatch_breaking(self, dispatcher: Any | None = None) -> dict[str, int]:
        """立即下发缓冲中的黑天鹅新闻，成功后从批量队列移除。"""
        if dispatcher is None:
            from services.data.src.notify.dispatcher import get_dispatcher

            dispatcher = get_dispatcher()

        with self._lock:
            breaking_items = [dict(item) for item in self._push_buffer if item.get("breaking")]

        if not breaking_items:
            return {"breaking_pushed": 0}

        from services.data.src.notify.dispatcher import DataEvent, NotifyType

        sent_items: list[dict[str, Any]] = []
        for item in breaking_items:
            event = DataEvent(
                event_code="news_breaking",
                notify_type=NotifyType.P0,
                title=item.get("title", "突发重大新闻"),
                body_md=self._build_breaking_body(item),
                body_rows=[
                    ("来源", str(item.get("source_cn") or item.get("source") or "")),
                    ("关键词", str(item.get("keyword_hit") or "")),
                ],
                source_name=str(item.get("uid") or item.get("source") or "news_breaking"),
                channels={"feishu"},
                bypass_quiet_hours=True,
            )
            if dispatcher.dispatch(event):
                sent_items.append(item)

        return {"breaking_pushed": self._mark_as_dispatched(sent_items)}

    @staticmethod
    def _build_batch_body(items: list[dict[str, Any]]) -> str:
        lines = []
        for item in items[:20]:
            source_cn = item.get("source_cn") or item.get("source") or ""
            source_tag = f" ({source_cn})" if source_cn else ""
            title = str(item.get("title") or "")[:180]
            prefix = "🚨" if item.get("breaking") else "•"
            if item.get("url"):
                lines.append(f"{prefix} [{title}]({item['url']}){source_tag}")
            else:
                lines.append(f"{prefix} {title}{source_tag}")
        hidden = len(items) - min(len(items), 20)
        if hidden > 0:
            lines.append(f"… 其余 {hidden} 条已合并在本批次中")
        return "\n".join(lines)

    def _build_batch_event(self, items: list[dict[str, Any]]) -> Any:
        from services.data.src.notify.dispatcher import DataEvent, NotifyType

        batch_hash = hashlib.md5(
            "|".join(sorted(str(item.get("uid") or "") for item in items)).encode("utf-8")
        ).hexdigest()
        breaking_count = sum(1 for item in items if item.get("breaking"))
        market_count = sum(1 for item in items if item.get("market_related"))
        title_suffix = datetime.now(CN_TZ).strftime("%H:%M")
        title = f"新闻摘要 {title_suffix}"
        if breaking_count:
            title += f"（含突发 {breaking_count} 条）"

        return DataEvent(
            event_code="news_batch_summary",
            notify_type=NotifyType.NEWS,
            title=title,
            body_md=self._build_batch_body(items),
            body_rows=[
                ("摘要条数", str(len(items))),
                ("行业相关", str(market_count)),
                ("突发新闻", str(breaking_count)),
            ],
            trace_rows=[
                ("累计采集", str(self._total_collected)),
                ("累计清洗", str(self._total_cleaned)),
                ("已推送", str(self._total_pushed)),
                ("去重缓存", str(len(self._dispatched_uids))),
            ],
            source_name=f"news_batch:{batch_hash}",
            channels={"feishu"},
        )

    def flush(
        self,
        *,
        dispatcher: Any | None = None,
        now: datetime | None = None,
    ) -> dict[str, int]:
        """发送当前新闻缓冲区的一条合并摘要通知。"""
        if dispatcher is None:
            from services.data.src.notify.dispatcher import get_dispatcher

            dispatcher = get_dispatcher()

        breaking_stats = self.dispatch_breaking(dispatcher)

        with self._lock:
            items = [dict(item) for item in self._push_buffer if not item.get("breaking")]

        if not items:
            return {
                "pushed": 0,
                "breaking_pushed": breaking_stats.get("breaking_pushed", 0),
                "buffer_size": self.stats["buffer_size"],
            }

        from services.data.src.notify.dispatcher import NotifyType, _is_quiet_hours_for_type

        if _is_quiet_hours_for_type(NotifyType.NEWS, now):
            return {
                "pushed": 0,
                "breaking_pushed": breaking_stats.get("breaking_pushed", 0),
                "deferred": len(items),
                "buffer_size": self.stats["buffer_size"],
            }

        event = self._build_batch_event(items)
        if not dispatcher.dispatch(event):
            return {
                "pushed": 0,
                "breaking_pushed": breaking_stats.get("breaking_pushed", 0),
                "failed": len(items),
                "buffer_size": self.stats["buffer_size"],
            }

        pushed = self._mark_as_dispatched(items)
        return {
            "pushed": pushed,
            "breaking_pushed": breaking_stats.get("breaking_pushed", 0),
            "buffer_size": self.stats["buffer_size"],
        }

    def flush_batch(
        self,
        *,
        dispatcher: Any | None = None,
        now: datetime | None = None,
    ) -> dict[str, int]:
        """兼容旧接口，统一走同一条新闻摘要推送路径。"""
        return self.flush(dispatcher=dispatcher, now=now)

    @property
    def stats(self) -> dict[str, int]:
        return {
            "total_collected": self._total_collected,
            "total_cleaned": self._total_cleaned,
            "total_pushed": self._total_pushed,
            "dedup_cache_size": len(self._dispatched_uids),
            "buffer_size": len(self._push_buffer),
        }
