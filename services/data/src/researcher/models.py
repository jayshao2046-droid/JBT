"""数据模型 — 研究员子系统"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SymbolResearch(BaseModel):
    """品种级研究结果"""
    symbol: str
    trend: str = Field(..., description="趋势判断：偏多/偏空/震荡/观望")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心度 0~1")
    key_factors: List[str] = Field(default_factory=list, description="关键因素")
    overnight_context: Optional[str] = Field(None, description="隔夜背景")
    risk_note: Optional[str] = Field(None, description="主要风险点")
    news_highlights: List[str] = Field(default_factory=list, description="新闻要点")
    position_change: Optional[Dict[str, int]] = Field(None, description="持仓变化 {long: +/-N, short: +/-N}")
    think_chain: Optional[str] = Field(None, description="qwen3 <think> 推理链（保留完整推理过程供审计）")


class ResearchReport(BaseModel):
    """研究报告主体"""
    report_id: str = Field(..., description="报告ID RPT-YYYYMMDD-时段-序号")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    segment: str = Field(..., description="时段：盘前/午间/盘后/夜盘")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    model: str = Field(default="qwen3:14b", description="使用的模型")

    futures_summary: Dict[str, Any] = Field(default_factory=dict, description="期货综述")
    stocks_summary: Dict[str, Any] = Field(default_factory=dict, description="股票综述")
    crawler_stats: Dict[str, Any] = Field(default_factory=dict, description="爬虫统计")

    previous_report_id: Optional[str] = Field(None, description="上期报告ID")
    change_highlights: List[str] = Field(default_factory=list, description="变化要点")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StagingRecord(BaseModel):
    """暂存区记录"""
    symbol: str
    last_read_ts: datetime = Field(..., description="最后读取时间戳")
    data_count: int = Field(default=0, description="本次读取数据条数")
    data_hash: Optional[str] = Field(None, description="数据哈希（用于去重）")
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SourceConfig(BaseModel):
    """采集源配置"""
    source_id: str = Field(..., description="源ID")
    name: str = Field(..., description="源名称")
    url_pattern: str = Field(..., description="URL 模板")
    mode: str = Field(..., description="模式：code/browser")
    parser: str = Field(..., description="解析器名称")
    schedule: List[str] = Field(default_factory=list, description="适用时段：盘前/午间/盘后/夜盘")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=5, description="优先级 1~10")
    timeout: int = Field(default=30, description="超时秒数")

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "eastmoney_futures",
                "name": "东方财富期货频道",
                "url_pattern": "https://futures.eastmoney.com/news/",
                "mode": "code",
                "parser": "eastmoney_futures",
                "schedule": ["盘前", "午间", "盘后"],
                "enabled": True,
                "priority": 8,
                "timeout": 30
            }
        }
