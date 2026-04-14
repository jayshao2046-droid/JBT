"""研究员 REST API — 报告查询 / 采集源 CRUD / 状态 / 手动触发"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json
from pathlib import Path
import sys

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from researcher.config import ResearcherConfig
from researcher.models import SourceConfig
from researcher.crawler.source_registry import SourceRegistry
from researcher.scheduler import ResearcherScheduler

router = APIRouter(prefix="/api/v1/researcher", tags=["researcher"])

# 全局实例
_source_registry = None
_scheduler = None


def get_source_registry() -> SourceRegistry:
    """获取采集源注册表"""
    global _source_registry
    if _source_registry is None:
        yaml_path = os.path.join(os.getcwd(), "configs", "researcher_sources.yaml")
        _source_registry = SourceRegistry(yaml_path=yaml_path if os.path.exists(yaml_path) else None)
    return _source_registry


def get_scheduler() -> ResearcherScheduler:
    """获取调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ResearcherScheduler()
    return _scheduler


@router.get("/report/latest")
async def get_latest_report() -> Dict[str, Any]:
    """获取最新一期研究员报告（JSON 决策版）"""
    reports_dir = Path(ResearcherConfig.REPORTS_DIR)

    if not reports_dir.exists():
        raise HTTPException(status_code=404, detail="No reports found")

    # 遍历所有日期目录，找到最新报告
    all_reports = []
    for date_dir in sorted(reports_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue

        for segment_file in date_dir.glob("*.json"):
            report_path = date_dir / segment_file
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
                all_reports.append(report)

        if all_reports:
            break  # 只取最新日期的报告

    if not all_reports:
        raise HTTPException(status_code=404, detail="No reports found")

    # 按生成时间排序，取最新
    all_reports.sort(key=lambda x: x["generated_at"], reverse=True)
    return all_reports[0]


@router.get("/report/{date}")
async def get_reports_by_date(date: str) -> Dict[str, Any]:
    """获取指定日期的研究员报告列表"""
    date_dir = Path(ResearcherConfig.REPORTS_DIR) / date

    if not date_dir.exists():
        raise HTTPException(status_code=404, detail=f"No reports found for date {date}")

    segments = []
    for segment_file in date_dir.glob("*.json"):
        with open(segment_file, "r", encoding="utf-8") as f:
            report = json.load(f)
            segments.append({
                "segment": report["segment"],
                "report_id": report["report_id"],
                "generated_at": report["generated_at"]
            })

    return {
        "date": date,
        "segments": segments
    }


@router.get("/report/{date}/{segment}")
async def get_report_by_date_segment(date: str, segment: str) -> Dict[str, Any]:
    """获取指定日期+时段的报告"""
    report_path = Path(ResearcherConfig.REPORTS_DIR) / date / f"{segment}.json"

    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"Report not found: {date} {segment}")

    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """研究员子系统状态"""
    scheduler = get_scheduler()

    # 获取最新报告信息
    try:
        latest_report = await get_latest_report()
        last_run = {
            "report_id": latest_report["report_id"],
            "segment": latest_report["segment"],
            "generated_at": latest_report["generated_at"]
        }
    except HTTPException:
        last_run = None

    return {
        "status": "running",
        "last_run": last_run,
        "next_schedule": {
            "盘前": "08:30",
            "午间": "11:35",
            "盘后": "15:20",
            "夜盘": "23:10"
        },
        "resource_status": {
            "alienware_reachable": True,  # TODO: 实际检查
            "ollama_available": True  # TODO: 实际检查
        }
    }


@router.post("/trigger")
async def trigger_research(segment: str = Query(..., description="时段：盘前/午间/盘后/夜盘")) -> Dict[str, Any]:
    """手动触发一次指定时段的研究"""
    if segment not in ["盘前", "午间", "盘后", "夜盘"]:
        raise HTTPException(status_code=400, detail="Invalid segment")

    scheduler = get_scheduler()
    result = await scheduler.execute_segment(segment)

    return result


@router.get("/sources")
async def get_sources() -> List[Dict[str, Any]]:
    """获取采集源列表"""
    registry = get_source_registry()
    sources = registry.get_all_sources()

    return [s.dict() for s in sources]


@router.post("/sources")
async def create_source(source: SourceConfig) -> Dict[str, Any]:
    """新增采集源"""
    registry = get_source_registry()

    # 检查是否已存在
    if registry.get_source(source.source_id):
        raise HTTPException(status_code=400, detail=f"Source {source.source_id} already exists")

    registry.add_source(source)

    return {"message": "Source created", "source_id": source.source_id}


@router.put("/sources/{source_id}")
async def update_source(source_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """更新采集源配置"""
    registry = get_source_registry()

    if not registry.get_source(source_id):
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    registry.update_source(source_id, updates)

    return {"message": "Source updated", "source_id": source_id}


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str) -> Dict[str, Any]:
    """删除采集源"""
    registry = get_source_registry()

    if not registry.get_source(source_id):
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    registry.remove_source(source_id)

    return {"message": "Source deleted", "source_id": source_id}
