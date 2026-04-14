"""配置管理 — 研究员子系统"""

import os
from typing import List, Dict, Any


class ResearcherConfig:
    """研究员配置"""

    # Alienware Ollama 配置
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://192.168.31.224:11434")
    OLLAMA_MODEL = "qwen3:14b"
    OLLAMA_TEMPERATURE = 0.3
    OLLAMA_NUM_CTX = 8192
    OLLAMA_TIMEOUT = 120.0

    # Mini data API 配置
    DATA_API_URL = os.getenv("DATA_API_URL", "http://192.168.31.76:8105")

    # 期货品种列表 — Mini 主力连续合约（KQ.m@ 格式，Mini API 内部解析为 KQ_m_ 格式）
    FUTURES_SYMBOLS = [
        # 上期所 SHFE
        "KQ.m@SHFE.rb", "KQ.m@SHFE.hc", "KQ.m@SHFE.cu", "KQ.m@SHFE.al",
        "KQ.m@SHFE.zn", "KQ.m@SHFE.pb", "KQ.m@SHFE.ni", "KQ.m@SHFE.sn",
        "KQ.m@SHFE.au", "KQ.m@SHFE.ag", "KQ.m@SHFE.ru", "KQ.m@SHFE.bu",
        "KQ.m@SHFE.sp", "KQ.m@SHFE.fu", "KQ.m@SHFE.ss",
        # 大商所 DCE
        "KQ.m@DCE.i", "KQ.m@DCE.j", "KQ.m@DCE.jm", "KQ.m@DCE.a",
        "KQ.m@DCE.m", "KQ.m@DCE.y", "KQ.m@DCE.p", "KQ.m@DCE.c",
        "KQ.m@DCE.cs", "KQ.m@DCE.pp", "KQ.m@DCE.v", "KQ.m@DCE.l",
        "KQ.m@DCE.eg", "KQ.m@DCE.eb", "KQ.m@DCE.pg", "KQ.m@DCE.rr",
        "KQ.m@DCE.lh", "KQ.m@DCE.jd",
        # 郑商所 CZCE
        "KQ.m@CZCE.TA", "KQ.m@CZCE.MA", "KQ.m@CZCE.SR", "KQ.m@CZCE.CF",
        "KQ.m@CZCE.RM", "KQ.m@CZCE.OI", "KQ.m@CZCE.FG", "KQ.m@CZCE.SA",
        "KQ.m@CZCE.AP", "KQ.m@CZCE.PF", "KQ.m@CZCE.PK", "KQ.m@CZCE.SM",
        "KQ.m@CZCE.SF", "KQ.m@CZCE.ZC", "KQ.m@CZCE.WH", "KQ.m@CZCE.UR",
        "KQ.m@CZCE.CJ",
        # 中金所 CFFEX
        "KQ.m@CFFEX.IF", "KQ.m@CFFEX.IH", "KQ.m@CFFEX.IC", "KQ.m@CFFEX.IM",
        "KQ.m@CFFEX.T", "KQ.m@CFFEX.TF", "KQ.m@CFFEX.TL", "KQ.m@CFFEX.TS",
        # 上期能源 INE
        "KQ.m@INE.sc", "KQ.m@INE.lu", "KQ.m@INE.nr", "KQ.m@INE.bc",
        # 广期所 GFEX
        "KQ.m@GFEX.si", "KQ.m@GFEX.lc",
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

    # 报告存储配置
    REPORTS_DIR = os.path.join(os.getcwd(), "runtime", "researcher", "reports")

    # 报告索引数据库（减量化索引，复用 staging.db）
    REPORTS_DB = STAGING_DB

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
