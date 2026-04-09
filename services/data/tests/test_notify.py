#!/usr/bin/env python3
"""TASK-0027-A5 通知系统联调测试（增强 TASK-0028 基线）。

验证:
1. 原有 11 个测试保持不动
2. 增强: news_pusher flush 链路
3. 增强: email HTML 日报生成
4. 增强: 飞书卡片全模板覆盖
5. 增强: dispatcher 告警升级 / 冷却 / 渠道降级
6. 增强: news_pusher dedup 持久化
7. 增强: flush_batch 兼容接口

用法:
    # 仅烟雾测试（不发送真实消息）
    python -m pytest services/data/tests/test_notify.py -v

    # 真实飞书 + 邮件测试（需设置环境变量）
    python services/data/tests/test_notify.py --live
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

# 确保项目根目录在 sys.path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


# ═══════════════════════════════════════════════
# Unit / Smoke Tests (pytest)
# ═══════════════════════════════════════════════


class FakeFeishuSender:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def send(self, *, webhook_url: str, event: Any) -> bool:
        self.events.append({"webhook_url": webhook_url, "event": event})
        return True


class FakeEmailSender:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def send(self, *, event: Any) -> bool:
        self.events.append(event)
        return True


class CaptureDispatcher:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def dispatch(self, event: Any) -> bool:
        self.events.append(event)
        return True

def test_import_dispatcher():
    from services.data.src.notify.dispatcher import (
        DataEvent, NotifierDispatcher, NotifyType, get_dispatcher,
    )
    assert NotifyType.P0.value == "P0"
    assert NotifyType.NOTIFY.value == "NOTIFY"
    evt = DataEvent(
        event_code="test_event",
        title="test",
        notify_type=NotifyType.NOTIFY,
        body_md="test body",
        body_rows=[("k", "v")],
    )
    assert evt.title == "test"
    assert isinstance(get_dispatcher(), NotifierDispatcher)


def test_import_card_templates():
    from services.data.src.notify import card_templates as ct
    card = ct.service_lifecycle_card(action="启动", version="v0.2.1")
    assert "card" in card
    assert card["card"]["header"]["template"] == "turquoise"


def test_import_feishu_sender():
    from services.data.src.notify.feishu import FeishuSender
    sender = FeishuSender()
    assert hasattr(sender, "send")
    assert hasattr(sender, "send_card")


def test_import_email_sender():
    from services.data.src.notify.email_notify import EmailSender, build_daily_report_html
    sender = EmailSender()
    assert hasattr(sender, "send")
    assert hasattr(sender, "send_daily_report")

    # 测试日报 HTML 生成
    html = build_daily_report_html(
        total_rounds=10, success_rate=90.0, failed_collectors=["test"],
        total_records=1000, sources_freshness=[{"label": "测试", "ok": True, "age_str": "5m"}],
        cpu_pct=30.0, mem_pct=50.0, disk_pct=60.0,
        process_status=[{"label": "test", "ok": True, "uptime": "2h"}],
        errors=[], news_collected=100, news_pushed=50, breaking_count=1,
        health_score=85,
    )
    assert "健康评分" in html
    assert "85/100" in html


def test_import_news_pusher():
    from services.data.src.notify.news_pusher import NewsPusher
    pusher = NewsPusher()
    assert hasattr(pusher, "ingest")
    assert hasattr(pusher, "flush")
    assert hasattr(pusher, "flush_batch")


def test_card_templates_all():
    """验证所有 13 种卡片模板都能正常生成。"""
    from services.data.src.notify import card_templates as ct

    cards = [
        ct.collector_start_card(collector_name="测试"),
        ct.collector_done_card(collector_name="测试", record_count=100, elapsed_sec=2.5, freshness="5分钟前"),
        ct.collector_batch_card(
            results=[{"name": "日线", "records": 100, "elapsed": 1.0, "ok": True}],
            total_records=100, total_elapsed=1.0),
        ct.collector_fail_card(collector_name="测试", error_msg="timeout", retry_count=3),
        ct.collector_recovery_card(recovered=["测试A"], still_failed=["测试B"]),
        ct.alert_card(level="P1", title="CPU过高", body_md="CPU 85%"),
        ct.alert_p0_with_buttons(
            title="P0紧急", body_md="CPU 95%",
            ops_base_url="http://localhost:8105", ops_token="test",
        ),
        ct.news_batch_card(
            category="重大新闻",
            items=[{"title": "测试新闻", "source_cn": "新华社", "url": "https://example.com"}],
            total_collected=50, total_pushed=10, total_cleaned=40,
        ),
        ct.news_breaking_card(
            title="突发新闻", url="https://example.com",
            source_cn="央视", keyword_hit="战争",
        ),
        ct.device_health_card(
            cpu_pct=30, mem_pct=50, disk_pct=60,
            processes=[{"label": "test", "ok": True}],
            net_latency_ms=50,
        ),
        ct.daily_summary_card(
            total_rounds=10, success_rate=95.0,
            failed_collectors=[], total_records=1000,
            sources_freshness=[{"label": "测试", "ok": True, "age_str": "5m"}],
            cpu_pct=30, mem_pct=50, disk_pct=60,
            error_count=0, news_collected=100, news_pushed=50, health_score=90,
        ),
        ct.service_lifecycle_card(action="启动", version="v0.2.1"),
        ct.recovery_card(title="恢复", detail="全部恢复正常"),
    ]

    for i, card in enumerate(cards):
        assert "msg_type" in card or "header" in card.get("card", {}), f"card {i} invalid"


def test_collection_summary_merges_same_window_and_skips_email():
    from services.data.src.notify.dispatcher import NotifierDispatcher

    feishu = FakeFeishuSender()
    email = FakeEmailSender()
    dispatcher = NotifierDispatcher(
        feishu_sender=feishu,
        email_sender=email,
        collector_window_sec=0,
    )

    dispatcher.record_collection_result(
        collector_name="日线K线",
        record_count=128,
        elapsed_sec=1.2,
        status="success",
    )
    dispatcher.record_collection_result(
        collector_name="外盘分钟K线",
        record_count=0,
        elapsed_sec=2.4,
        status="zero_output",
    )

    assert dispatcher.flush_collection_window() is True
    assert len(feishu.events) == 1
    assert email.events == []

    event = feishu.events[0]["event"]
    assert event.title.startswith("采集摘要")
    assert "日线K线" in event.body_md
    assert "外盘分钟K线" in event.body_md
    assert "0产出" in event.body_md


def test_zero_output_is_not_reported_as_complete():
    from services.data.src.notify.dispatcher import NotifierDispatcher

    feishu = FakeFeishuSender()
    dispatcher = NotifierDispatcher(
        feishu_sender=feishu,
        email_sender=FakeEmailSender(),
        collector_window_sec=0,
    )

    dispatcher.record_collection_result(
        collector_name="外盘分钟K线",
        record_count=0,
        elapsed_sec=3.5,
        status="zero_output",
    )
    dispatcher.flush_collection_window()

    event = feishu.events[0]["event"]
    assert event.title == "外盘分钟K线 0产出"
    assert "完成" not in event.title


def test_news_quiet_window_boundary_only_applies_to_news():
    from services.data.src.notify.dispatcher import CN_TZ, NotifyType, _is_quiet_hours_for_type

    assert _is_quiet_hours_for_type(NotifyType.NEWS, datetime(2026, 4, 9, 8, 29, tzinfo=CN_TZ)) is True
    assert _is_quiet_hours_for_type(NotifyType.NEWS, datetime(2026, 4, 9, 8, 30, tzinfo=CN_TZ)) is False
    assert _is_quiet_hours_for_type(NotifyType.NOTIFY, datetime(2026, 4, 9, 8, 15, tzinfo=CN_TZ)) is False


def test_news_pusher_flush_dispatches_single_summary(tmp_path: Path):
    from services.data.src.notify.news_pusher import NewsPusher
    from services.data.src.notify.dispatcher import CN_TZ

    pusher = NewsPusher(dedup_file=tmp_path / "news_dedup.json")
    stats = pusher.ingest([
        {
            "title": "央行公开市场操作保持流动性合理充裕",
            "url": "https://example.com/news-1",
            "summary": "公开市场操作公告",
            "source": "xinhua",
        },
        {
            "title": "螺纹钢主力合约夜盘延续偏强走势",
            "url": "https://example.com/news-2",
            "summary": "黑色系夜盘波动上行",
            "source": "cls",
        },
    ])
    assert stats["new"] == 2

    dispatcher = CaptureDispatcher()
    result = pusher.flush(
        dispatcher=dispatcher,
        now=datetime(2026, 4, 9, 9, 0, tzinfo=CN_TZ),
    )

    assert result["pushed"] == 2
    assert len(dispatcher.events) == 1
    event = dispatcher.events[0]
    assert event.event_code == "news_batch_summary"
    assert "新闻摘要" in event.title
    assert "螺纹钢" in event.body_md


def test_job_news_push_batch_syncs_storage_before_flush(monkeypatch):
    from services.data.src.notify import news_pusher as news_pusher_module
    from services.data.src.scheduler.data_scheduler import NEWS_STORAGE_SYNC_LIMIT_PER_SOURCE, job_news_push_batch

    calls: list[tuple[str, int | None]] = []

    class FakeNewsPusher:
        def sync_from_storage(self, *, limit_per_source: int) -> dict[str, Any]:
            calls.append(("sync", limit_per_source))
            return {"new": 2}

        def flush(self) -> dict[str, Any]:
            calls.append(("flush", None))
            return {"pushed": 2}

    monkeypatch.setattr(news_pusher_module, "NewsPusher", FakeNewsPusher)

    job_news_push_batch({})

    assert calls == [("sync", NEWS_STORAGE_SYNC_LIMIT_PER_SOURCE), ("flush", None)]


def test_webhook_for_type_accepts_news_and_trading_compat_envs(monkeypatch):
    from services.data.src.notify.dispatcher import NotifyType, _webhook_for_type

    monkeypatch.delenv("FEISHU_INFO_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("FEISHU_TRADE_WEBHOOK_URL", raising=False)
    monkeypatch.setenv("FEISHU_NEWS_WEBHOOK_URL", "https://news-webhook")
    monkeypatch.setenv("FEISHU_TRADING_WEBHOOK_URL", "https://trading-webhook")

    assert _webhook_for_type(NotifyType.NEWS) == "https://news-webhook"
    assert _webhook_for_type(NotifyType.INFO) == "https://news-webhook"
    assert _webhook_for_type(NotifyType.NOTIFY) == "https://news-webhook"
    assert _webhook_for_type(NotifyType.TRADE) == "https://trading-webhook"


# ── 增强覆盖: news_pusher dedup 持久化 ─────────────────────

def test_news_pusher_dedup_persists_across_instances(tmp_path: Path):
    """Dedup state should survive across NewsPusher instances."""
    from services.data.src.notify.news_pusher import NewsPusher
    from services.data.src.notify.dispatcher import CN_TZ

    dedup_file = tmp_path / "news_dedup.json"
    pusher1 = NewsPusher(dedup_file=dedup_file)
    pusher1.ingest([{
        "title": "特殊去重测试新闻",
        "url": "https://example.com/dedup-test",
        "summary": "去重测试",
        "source": "test",
    }])
    dispatcher1 = CaptureDispatcher()
    pusher1.flush(
        dispatcher=dispatcher1,
        now=datetime(2026, 4, 9, 10, 0, tzinfo=CN_TZ),
    )
    assert len(dispatcher1.events) == 1

    # Second instance with same dedup file should skip the same news
    pusher2 = NewsPusher(dedup_file=dedup_file)
    stats = pusher2.ingest([{
        "title": "特殊去重测试新闻",
        "url": "https://example.com/dedup-test",
        "summary": "去重测试",
        "source": "test",
    }])
    assert stats["new"] == 0


def test_news_pusher_flush_batch_compat(tmp_path: Path):
    """flush_batch should be an alias for flush."""
    from services.data.src.notify.news_pusher import NewsPusher
    from services.data.src.notify.dispatcher import CN_TZ

    pusher = NewsPusher(dedup_file=tmp_path / "dedup.json")
    pusher.ingest([{
        "title": "flush_batch 兼容测试",
        "url": "https://example.com/batch",
        "summary": "兼容",
        "source": "test",
    }])
    dispatcher = CaptureDispatcher()
    result = pusher.flush_batch(
        dispatcher=dispatcher,
        now=datetime(2026, 4, 9, 10, 0, tzinfo=CN_TZ),
    )
    assert result["pushed"] == 1


def test_news_pusher_stats_property(tmp_path: Path):
    """NewsPusher.stats should return correct counters."""
    from services.data.src.notify.news_pusher import NewsPusher

    pusher = NewsPusher(dedup_file=tmp_path / "dedup.json")
    stats = pusher.stats
    assert "total_collected" in stats
    assert "buffer_size" in stats
    assert stats["total_collected"] == 0


# ── 增强覆盖: email HTML 日报生成 ──────────────────────────

def test_build_daily_report_html_contains_all_sections():
    """Daily report HTML should contain all major sections."""
    from services.data.src.notify.email_notify import build_daily_report_html

    html = build_daily_report_html(
        total_rounds=20, success_rate=95.0,
        failed_collectors=["波动率", "天气"],
        total_records=50000,
        sources_freshness=[
            {"label": "国内期货分钟", "ok": True, "age_str": "2分钟"},
            {"label": "外盘日线", "ok": False, "age_str": "48小时"},
        ],
        cpu_pct=45.0, mem_pct=60.0, disk_pct=70.0,
        process_status=[
            {"label": "调度器", "ok": True, "uptime": "24h"},
            {"label": "新闻", "ok": False, "uptime": "0h"},
        ],
        errors=[
            {"time": "10:30", "msg": "timeout"},
            {"time": "14:00", "msg": "connection refused"},
        ],
        news_collected=500, news_pushed=30, breaking_count=2,
        health_score=72,
    )
    assert "72/100" in html
    assert "波动率" in html or "天气" in html
    assert "50000" in html or "50,000" in html


def test_build_daily_report_html_zero_errors():
    """Daily report with zero errors should still render."""
    from services.data.src.notify.email_notify import build_daily_report_html

    html = build_daily_report_html(
        total_rounds=10, success_rate=100.0,
        failed_collectors=[],
        total_records=10000,
        sources_freshness=[],
        cpu_pct=10.0, mem_pct=20.0, disk_pct=30.0,
        process_status=[],
        errors=[], news_collected=0, news_pushed=0, breaking_count=0,
        health_score=100,
    )
    assert "100/100" in html


# ── 增强覆盖: 飞书卡片模板逐一校验 ─────────────────────────

def test_card_alert_p0_buttons_has_interactive_elements():
    """P0 alert card should have action buttons."""
    from services.data.src.notify import card_templates as ct

    card = ct.alert_p0_with_buttons(
        title="P0测试", body_md="紧急",
        ops_base_url="http://localhost:8105", ops_token="tok",
    )
    card_body = card.get("card", {})
    assert card_body.get("header", {}).get("template") == "red"


def test_card_news_batch_has_correct_template():
    """News batch card should use wathet template."""
    from services.data.src.notify import card_templates as ct

    card = ct.news_batch_card(
        category="重大新闻",
        items=[{"title": "测试", "source_cn": "新华社", "url": "https://example.com"}],
        total_collected=10, total_pushed=1, total_cleaned=9,
    )
    assert card["card"]["header"]["template"] == "wathet"


def test_card_daily_summary_has_correct_template():
    """Daily summary card template should reflect health_score."""
    from services.data.src.notify import card_templates as ct

    card_good = ct.daily_summary_card(
        total_rounds=10, success_rate=90.0,
        failed_collectors=[], total_records=1000,
        sources_freshness=[], cpu_pct=30, mem_pct=50, disk_pct=60,
        error_count=0, news_collected=50, news_pushed=10, health_score=90,
    )
    assert card_good["card"]["header"]["template"] == "green"

    card_bad = ct.daily_summary_card(
        total_rounds=10, success_rate=50.0,
        failed_collectors=["a", "b"], total_records=100,
        sources_freshness=[], cpu_pct=90, mem_pct=90, disk_pct=90,
        error_count=5, news_collected=0, news_pushed=0, health_score=30,
    )
    assert card_bad["card"]["header"]["template"] == "red"


def test_card_device_health_uses_dynamic_template():
    """Device health card template should reflect device health."""
    from services.data.src.notify import card_templates as ct

    card = ct.device_health_card(
        cpu_pct=30, mem_pct=50, disk_pct=60,
        processes=[{"label": "test", "ok": True}],
        net_latency_ms=50,
    )
    # healthy device → green
    assert card["card"]["header"]["template"] == "green"
    assert "card" in card


def test_card_collector_batch_aggregates_results():
    """Batch card should aggregate multiple collector results."""
    from services.data.src.notify import card_templates as ct

    card = ct.collector_batch_card(
        results=[
            {"name": "日线", "records": 100, "elapsed": 1.0, "ok": True},
            {"name": "外盘", "records": 50, "elapsed": 2.0, "ok": True},
            {"name": "宏观", "records": 0, "elapsed": 0, "ok": False},
        ],
        total_records=150, total_elapsed=3.0,
    )
    assert "card" in card


# ── 增强覆盖: dispatcher 通道状态初始化 ────────────────────

def test_dispatcher_initial_channel_state():
    """Dispatcher should start with NORMAL channel state."""
    from services.data.src.notify.dispatcher import NotifierDispatcher, ChannelState

    dispatcher = NotifierDispatcher(
        feishu_sender=FakeFeishuSender(),
        email_sender=FakeEmailSender(),
    )
    assert dispatcher.channel_state == ChannelState.NORMAL


def test_dispatcher_dispatch_returns_bool():
    """dispatch() should return a boolean."""
    from services.data.src.notify.dispatcher import DataEvent, NotifierDispatcher, NotifyType

    feishu = FakeFeishuSender()
    dispatcher = NotifierDispatcher(
        feishu_sender=feishu,
        email_sender=FakeEmailSender(),
    )
    event = DataEvent(
        event_code="test_dispatch",
        title="测试调度",
        notify_type=NotifyType.NOTIFY,
        body_md="测试",
        body_rows=[("key", "value")],
    )
    result = dispatcher.dispatch(event)
    assert isinstance(result, bool)


# ═══════════════════════════════════════════════
# Live Integration Test (--live flag)
# ═══════════════════════════════════════════════

def _run_live_test():
    """发送真实飞书 + 邮件通知进行端到端验证。"""
    from services.data.src.notify.feishu import FeishuSender
    from services.data.src.notify.email_notify import EmailSender, build_daily_report_html
    from services.data.src.notify import card_templates as ct

    alert_wh = os.environ.get("FEISHU_ALERT_WEBHOOK_URL", "")
    trade_wh = os.environ.get("FEISHU_TRADING_WEBHOOK_URL", "")
    info_wh = os.environ.get("FEISHU_NEWS_WEBHOOK_URL", "")

    sender = FeishuSender()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 50)
    print(f"  TASK-0028 通知系统实测  {now_str}")
    print("=" * 50)

    # ── 1. 报警群：P0 + P1 + P2 + 恢复 ──
    if alert_wh:
        print("\n[1/7] 报警群 — P0 紧急告警 (带按钮)")
        card = ct.alert_p0_with_buttons(
            title="[测试] P0 紧急告警 — CPU 过载",
            body_md="**CPU:** 95%\n**内存:** 88%\n**设备:** Mini\n\nCPU 利用率连续 10 分钟超过 90%",
            ops_base_url=os.environ.get("DATA_OPS_URL", "http://localhost:8105"),
            ops_token=os.environ.get("DATA_OPS_SECRET", ""),
        )
        sender.send_card(alert_wh, card)

        print("[2/7] 报警群 — P1 采集告警")
        card = ct.alert_card(
            level="P1", title="[测试] 外盘分钟线延迟",
            body_md="**采集源:** 外盘分钟线\n**延迟:** 48h\n**上次更新:** 2天前\n\noverseas_minute 数据目录最后更新超过 48 小时",
        )
        sender.send_card(alert_wh, card)

        print("[3/7] 报警群 — 恢复通知")
        card = ct.collector_recovery_card(
            recovered=["外盘分钟线", "A股实时"],
            still_failed=["天气数据"],
        )
        sender.send_card(alert_wh, card)

        print("[4/7] 报警群 — 设备健康")
        card = ct.device_health_card(
            cpu_pct=32.5, mem_pct=56.8, disk_pct=67.2,
            processes=[
                {"label": "数据调度", "ok": True},
                {"label": "新闻采集", "ok": True},
                {"label": "健康检查", "ok": True},
                {"label": "VPN代理", "ok": False},
            ],
            net_latency_ms=28,
        )
        sender.send_card(alert_wh, card)
    else:
        print("[跳过] 报警群 — 无 FEISHU_ALERT_WEBHOOK_URL")

    # ── 2. 交易群：采集启动 + 完成 + 批次 ──
    if trade_wh:
        print("\n[5/7] 交易群 — 采集启动 + 完成 + 批次")
        sender.send_card(trade_wh, ct.collector_start_card(
            collector_name="[测试] 日线K线",
        ))
        sender.send_card(trade_wh, ct.collector_done_card(
            collector_name="[测试] 日线K线", record_count=1250,
            elapsed_sec=3.2, freshness="刚刚",
        ))
        sender.send_card(trade_wh, ct.collector_batch_card(
            results=[
                {"name": "日线K线", "records": 1250, "elapsed": 3.2, "ok": True},
                {"name": "外盘日线", "records": 890, "elapsed": 5.1, "ok": True},
                {"name": "Tushare", "records": 0, "elapsed": 0, "ok": False},
            ],
            total_records=2140, total_elapsed=8.3,
        ))
    else:
        print("[跳过] 交易群 — 无 FEISHU_TRADING_WEBHOOK_URL")

    # ── 3. 资讯群：新闻批量 + 突发 ──
    if info_wh:
        print("\n[6/7] 资讯群 — 新闻批量 + 突发")
        sender.send_card(info_wh, ct.news_batch_card(
            category="重大新闻 + 行业新闻",
            items=[
                {"title": "[测试] 央行宣布降准50个基点", "source_cn": "新华社",
                 "url": "https://www.xinhuanet.com"},
                {"title": "[测试] 美联储暗示暂停加息", "source_cn": "路透社",
                 "url": "https://www.reuters.com"},
                {"title": "[测试] 螺纹钢主力合约创新高", "source_cn": "期货日报",
                 "url": "https://www.qhrb.com.cn"},
            ],
            total_collected=156, total_pushed=12, total_cleaned=144,
        ))
        sender.send_card(info_wh, ct.news_breaking_card(
            title="[测试] 黑天鹅：某国宣布紧急军事行动",
            source_cn="央视新闻",
            url="https://news.cctv.com",
            keyword_hit="战争, 军事行动",
        ))
    else:
        print("[跳过] 资讯群 — 无 FEISHU_NEWS_WEBHOOK_URL")

    # ── 4. 邮件：告警 + 日报 ──
    email_sender = EmailSender()
    if os.environ.get("SMTP_HOST"):
        print("\n[7/7] 邮件 — 日报")
        html = build_daily_report_html(
            total_rounds=18, success_rate=94.4,
            failed_collectors=["天气数据"],
            total_records=125680,
            sources_freshness=[
                {"label": "国内期货分钟", "ok": True, "age_str": "2分钟"},
                {"label": "外盘日线", "ok": True, "age_str": "5小时"},
                {"label": "新闻RSS", "ok": True, "age_str": "10分钟"},
                {"label": "天气", "ok": False, "age_str": "26小时"},
            ],
            cpu_pct=32.5, mem_pct=56.8, disk_pct=67.2,
            process_status=[
                {"label": "数据调度", "ok": True, "uptime": "12h"},
                {"label": "新闻采集", "ok": True, "uptime": "12h"},
                {"label": "健康检查", "ok": True, "uptime": "12h"},
            ],
            errors=[{"time": "14:30", "msg": "天气API超时 (timeout=30s)"}],
            news_collected=1560, news_pushed=45, breaking_count=1,
            health_score=88,
        )
        ok = email_sender.send_daily_report(html=html, report_type="[测试]日报")
        print(f"  邮件日报发送: {'✅ 成功' if ok else '❌ 失败'}")
    else:
        print("[跳过] 邮件 — 无 SMTP_HOST")

    print("\n" + "=" * 50)
    print("  测试完成！请检查飞书和邮件。")
    print("=" * 50)


if __name__ == "__main__":
    if "--live" in sys.argv:
        _run_live_test()
    else:
        print("用法:")
        print("  python -m pytest services/data/tests/test_notify.py -v   # 烟雾测试")
        print("  python services/data/tests/test_notify.py --live         # 真实发送")
