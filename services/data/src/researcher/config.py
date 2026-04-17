"""配置管理 — 研究员子系统"""

import os
from typing import List, Dict, Any


class ResearcherConfig:
    """研究员配置"""

    # Alienware Ollama 配置
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://192.168.31.223:11434")
    OLLAMA_MODEL = "qwen3:14b"
    OLLAMA_TEMPERATURE = 0.3
    OLLAMA_NUM_CTX = 8192
    # 安全修复：P2-3 - 从环境变量读取超时配置
    OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120.0"))

    # Mini data API 配置
    DATA_API_URL = os.getenv("DATA_API_URL", "http://192.168.31.76:8105")

    # 期货品种列表 — Jay.S 2026-04-15 确认的 35 个有4年以上连续数据品种
    # （KQ.m@ 格式，Mini API 内部解析为 KQ_m_ 格式）
    # SHFE(10): rb hc cu al zn au ag ru ss sp
    # DCE(15): i m pp v l c jd y p a jm j eb pg lh
    # CZCE(10): TA MA CF SR OI RM FG SA PF UR
    FUTURES_SYMBOLS = [
        # 上期所 SHFE (10)
        "KQ.m@SHFE.rb", "KQ.m@SHFE.hc", "KQ.m@SHFE.cu", "KQ.m@SHFE.al",
        "KQ.m@SHFE.zn", "KQ.m@SHFE.au", "KQ.m@SHFE.ag", "KQ.m@SHFE.ru",
        "KQ.m@SHFE.ss", "KQ.m@SHFE.sp",
        # 大商所 DCE (15)
        "KQ.m@DCE.i", "KQ.m@DCE.m", "KQ.m@DCE.pp", "KQ.m@DCE.v",
        "KQ.m@DCE.l", "KQ.m@DCE.c", "KQ.m@DCE.jd", "KQ.m@DCE.y",
        "KQ.m@DCE.p", "KQ.m@DCE.a", "KQ.m@DCE.jm", "KQ.m@DCE.j",
        "KQ.m@DCE.eb", "KQ.m@DCE.pg", "KQ.m@DCE.lh",
        # 郑商所 CZCE (10)
        "KQ.m@CZCE.TA", "KQ.m@CZCE.MA", "KQ.m@CZCE.CF", "KQ.m@CZCE.SR",
        "KQ.m@CZCE.OI", "KQ.m@CZCE.RM", "KQ.m@CZCE.FG", "KQ.m@CZCE.SA",
        "KQ.m@CZCE.PF", "KQ.m@CZCE.UR",
    ]

    # 股票：Mini stocks API 路径待修复，暂不从 API 拉取
    # 实际数据在 Mini /jbt/data/{symbol}/stock_minute/records.parquet（5368只）
    # 待 Mini stocks API 路径对齐后启用
    STOCK_SYMBOLS_TOP100: List[str] = []
    STOCK_SYMBOLS_WATCHLIST: List[str] = []

    @classmethod
    def get_all_stock_symbols(cls) -> List[str]:
        """获取全部股票列表（待 Mini stocks API 修复后启用）"""
        return cls.STOCK_SYMBOLS_TOP100 + cls.STOCK_SYMBOLS_WATCHLIST

    # 24/7 全天候调度（24 个整点，7天不停）
    # 飞书静默由 notifier._is_feishu_silent() 控制（23:30-08:00 不推送），推理持续
    HOURLY_SCHEDULE = [
        {"hour": 0, "label": "00:00", "cron": "0 0 * * *", "desc": "凌晨外盘"},
        {"hour": 1, "label": "01:00", "cron": "0 1 * * *", "desc": ""},
        {"hour": 2, "label": "02:00", "cron": "0 2 * * *", "desc": ""},
        {"hour": 3, "label": "03:00", "cron": "0 3 * * *", "desc": ""},
        {"hour": 4, "label": "04:00", "cron": "0 4 * * *", "desc": ""},
        {"hour": 5, "label": "05:00", "cron": "0 5 * * *", "desc": ""},
        {"hour": 6, "label": "06:00", "cron": "0 6 * * *", "desc": ""},
        {"hour": 7, "label": "07:00", "cron": "0 7 * * *", "desc": ""},
        {"hour": 8, "label": "08:00", "cron": "0 8 * * *", "desc": "开盘前准备"},
        {"hour": 9, "label": "09:00", "cron": "0 9 * * *", "desc": "开盘首小时"},
        {"hour": 10, "label": "10:00", "cron": "0 10 * * *", "desc": ""},
        {"hour": 11, "label": "11:00", "cron": "0 11 * * *", "desc": ""},
        {"hour": 12, "label": "12:00", "cron": "0 12 * * *", "desc": "午休"},
        {"hour": 13, "label": "13:00", "cron": "0 13 * * *", "desc": "午盘开盘"},
        {"hour": 14, "label": "14:00", "cron": "0 14 * * *", "desc": ""},
        {"hour": 15, "label": "15:00", "cron": "0 15 * * *", "desc": "收盘"},
        {"hour": 16, "label": "16:00", "cron": "0 16 * * *", "desc": "盘后总结"},
        {"hour": 17, "label": "17:00", "cron": "0 17 * * *", "desc": ""},
        {"hour": 18, "label": "18:00", "cron": "0 18 * * *", "desc": ""},
        {"hour": 19, "label": "19:00", "cron": "0 19 * * *", "desc": ""},
        {"hour": 20, "label": "20:00", "cron": "0 20 * * *", "desc": ""},
        {"hour": 21, "label": "21:00", "cron": "0 21 * * *", "desc": "夜盘开盘"},
        {"hour": 22, "label": "22:00", "cron": "0 22 * * *", "desc": ""},
        {"hour": 23, "label": "23:00", "cron": "0 23 * * *", "desc": "夜盘收盘（23:30后飞书静默）"},
    ]

    # 邮件日报配置
    EMAIL_MORNING_TRIGGER_HOUR = 16   # 16:00 研究完成后发早报
    EMAIL_EVENING_TRIGGER_HOUR = 23   # 23:00 研究完成后发晚报
    EMAIL_MORNING_HOURS = [8, 9, 10, 11, 13, 14, 15, 16]  # 早报汇总这些整点
    EMAIL_EVENING_HOURS = [21, 22, 23]                      # 晚报汇总这些整点

    # Mini data API 推送（研究报告推送到 Mini 供决策端消费）
    DATA_API_PUSH_URL = os.getenv("DATA_API_URL", "http://192.168.31.76:8105") + "/api/v1/researcher/reports"

    # 突发关键词（中文 + 英文）
    URGENT_KEYWORDS = [
        "紧急通知", "暂停交易", "重大政策", "黑天鹅",
        "强制平仓", "交易所公告", "政策调整", "突发事件",
        "halt", "suspend", "emergency", "breaking",
    ]

    # LEGACY: 四段时间定义（向后兼容，已废弃）
    SEGMENTS = {
        "盘前": {"cron": "30 8 * * 1-5", "description": "分析隔夜数据+外盘"},
        "午间": {"cron": "35 11 * * 1-5", "description": "上午盘汇总"},
        "盘后": {"cron": "20 15 * * 1-5", "description": "全天总结"},
        "夜盘": {"cron": "10 23 * * 1-5", "description": "夜盘收盘汇总"},
    }

    # 资源监控阈值
    RESOURCE_THRESHOLDS = {
        "gpu_usage_max": 90.0,  # GPU 使用率 > 90% 暂停
        "sim_trading_latency_max": 200.0,  # sim-trading 延迟 > 200ms 暂停
        "memory_usage_max": 85.0,  # 内存使用率 > 85% 暂停
    }

    # 暂存区配置
    STAGING_DIR = os.path.join(os.getcwd(), "runtime", "researcher", "staging")
    STAGING_DB = os.path.join(STAGING_DIR, "staging.db")

    # 报告存储配置（Alienware D 盘，供 phi4 决策端读取）
    REPORTS_DIR = os.getenv("REPORTS_DIR", "D:\\researcher_reports")

    # 日志目录（scheduler.log / daily_stats_*.json 共用）
    LOGS_DIR = os.path.join(os.getcwd(), "runtime", "researcher", "logs")

    # 报告索引数据库（减量化索引，复用 staging.db）
    REPORTS_DB = STAGING_DB

    # ── 决策端研报置信度评分标准 ──────────────────────────────────────────
    # 三维加权评分，由决策端计算后通过 POST /review/{report_id} 回写
    # 综合置信度 = Σ(维度得分 × weight)
    DECISION_CONFIDENCE_CRITERIA: Dict[str, Any] = {
        "news_relevance": {
            "weight": 0.30,
            "desc": "新闻相关性：爬取文章中含该品种/上下游关键词的比例",
            "scoring": "0=无相关新闻, 0.5=有相关新闻, 1=高质量相关新闻≥3条",
        },
        "trend_alignment": {
            "weight": 0.40,
            "desc": "趋势吻合度：qwen3 判断趋势与K线技术指标（MA/RSI/ATR）的一致性",
            "scoring": "0=完全相反, 0.5=中性/不确定, 1=完全吻合",
        },
        "cross_consistency": {
            "weight": 0.30,
            "desc": "板块一致性：同板块/上下游相关品种间逻辑一致程度",
            "scoring": "0=板块内明显矛盾, 0.5=部分一致, 1=高度一致",
        },
    }
    DECISION_CONFIDENCE_THRESHOLD_ACCEPT: float = 0.65  # ≥0.65 可直接采信
    DECISION_CONFIDENCE_THRESHOLD_WARN: float   = 0.40  # 0.40-0.64 建议人工复核
    # < 0.40 置信度过低，建议忽略

    # 执行超时保护
    EXECUTION_TIMEOUT = 15 * 60  # 单次执行 ≤15 分钟

    # LEGACY: 邮件日报配置（已废弃）
    EMAIL_MORNING_SEGMENTS = ["盘前", "午间"]  # 早报汇总这两段
    EMAIL_EVENING_SEGMENTS = ["盘后", "夜盘"]  # 晚报汇总这两段

    @classmethod
    def ensure_dirs(cls):
        """确保必要目录存在"""
        os.makedirs(cls.STAGING_DIR, exist_ok=True)
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
        os.makedirs(cls.LOGS_DIR, exist_ok=True)

    # ── Studio LLM 评级配置（2026-04-17 切换到 qwen3）─────────────────────
    SCORER_API_URL: str = os.getenv("SCORER_API_URL", "http://192.168.31.142:11434/api/generate")
    SCORER_MODEL: str = os.getenv("SCORER_MODEL", "qwen3:14b")  # 原为 phi4-reasoning:14b
    # 安全修复：P2-3 - 从环境变量读取超时配置
    SCORER_TIMEOUT: float = float(os.getenv("SCORER_TIMEOUT", "30.0"))  # 超时后 fallback 到数学算法

    # ── 网络请求超时配置（安全修复：P2-3）──────────────────────────────────
    HTTP_TIMEOUT_SHORT: float = float(os.getenv("HTTP_TIMEOUT_SHORT", "5.0"))    # 健康检查等快速请求
    HTTP_TIMEOUT_MEDIUM: float = float(os.getenv("HTTP_TIMEOUT_MEDIUM", "10.0"))  # 飞书推送等中等请求
    HTTP_TIMEOUT_LONG: float = float(os.getenv("HTTP_TIMEOUT_LONG", "15.0"))     # 数据拉取等长请求
    HTTP_TIMEOUT_TRANSLATE: float = float(os.getenv("HTTP_TIMEOUT_TRANSLATE", "20.0"))  # 翻译请求
    SMTP_TIMEOUT: float = float(os.getenv("SMTP_TIMEOUT", "30.0"))               # SMTP 连接超时

    # ── 推送策略 ──────────────────────────────────────────────────────────
    # True = 报告持久化到 Alienware D 盘，不推送 Mini（phi4 直接读取）
    PUSH_RETENTION_LOCAL: bool = True

    # ── 研究员健康度报告间隔 ──────────────────────────────────────────────
    HEALTH_INTERVAL_HOURS: int = 2
