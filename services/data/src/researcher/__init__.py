"""数据研究员子系统 — Alienware qwen3:14b + 双模式爬虫 + 四段报告

运行在 Alienware (192.168.31.224)，通过 qwen3:14b 对 Mini 采集的全量数据做增量预读归纳，
同时通过双模式爬虫采集期货/股票相关资讯，最终生成四段制双格式报告推送给决策端和 Jay.S。
"""

from .config import ResearcherConfig
from .models import ResearchReport, StagingRecord, SourceConfig, SymbolResearch
from .staging import StagingManager
from .summarizer import Summarizer
from .reporter import Reporter

__all__ = [
    "ResearcherConfig",
    "ResearchReport",
    "StagingRecord",
    "SourceConfig",
    "SymbolResearch",
    "StagingManager",
    "Summarizer",
    "Reporter",
]
