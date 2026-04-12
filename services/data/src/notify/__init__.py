"""JBT 数据端通知包 — dispatcher + feishu + email + news_pusher + card_templates。"""

from src.notify.dispatcher import (  # noqa: F401
    DataEvent,
    NotifierDispatcher,
    NotifyType,
    get_dispatcher,
)
from src.notify.feishu import FeishuSender  # noqa: F401
from src.notify.email_notify import EmailSender, build_daily_report_html  # noqa: F401
from src.notify.news_pusher import NewsPusher  # noqa: F401

__all__ = [
    "DataEvent",
    "NotifierDispatcher",
    "NotifyType",
    "get_dispatcher",
    "FeishuSender",
    "EmailSender",
    "build_daily_report_html",
    "NewsPusher",
]
