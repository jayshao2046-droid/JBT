"""研究员 REST API — 报告查询 / 采集源 CRUD / 状态 / 手动触发"""

import importlib
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import os
import json
import re
import logging
from pathlib import Path
import sys
from urllib.parse import urlparse

import httpx

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

logger = logging.getLogger(__name__)


def _validate_path_component(component: str, component_type: str = "generic") -> bool:
    """
    验证路径组件，防止路径遍历攻击

    Args:
        component: 路径组件（如日期、段名）
        component_type: 组件类型（"date" 或 "segment"）

    Returns:
        是否有效
    """
    # P1-4 修复：明确拒绝 .. 和 . 路径组件
    if component in ("..", ".") or "/" in component or "\\" in component:
        return False

    if component_type == "date":
        # 日期格式: YYYY-MM-DD
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', component))
    elif component_type == "segment":
        # 段名: 仅允许中文、字母、数字、下划线、连字符
        return bool(re.match(r'^[\u4e00-\u9fff\w-]+$', component))
    else:
        # 通用验证：不允许路径遍历字符
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', component))


def _safe_read_json_file(file_path: Path) -> Dict[str, Any]:
    """
    安全读取 JSON 文件，防止符号链接攻击和 TOCTOU

    Args:
        file_path: 文件路径

    Returns:
        JSON 数据

    Raises:
        HTTPException: 文件不存在、权限问题或格式错误
    """
    try:
        # P0-2 修复：先 resolve() 再检查符号链接，消除 TOCTOU 窗口
        file_path_resolved = file_path.resolve()

        # 检查是否为符号链接（在 resolve 后检查原始路径）
        if file_path.is_symlink():
            logger.warning(f"Attempted to read symlink: {file_path}")
            raise HTTPException(status_code=403, detail="Symbolic links not allowed")

        # 检查文件是否存在
        if not file_path_resolved.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # P0-3 修复：移除环境变量绕过，始终检查权限
        stat_info = file_path_resolved.stat()
        if stat_info.st_mode & 0o077:
            logger.warning(f"File has overly permissive permissions: {file_path_resolved}")
            raise HTTPException(status_code=403, detail="File has insecure permissions (world/group readable)")

        # 读取 JSON 文件（使用 resolved 路径）
        with open(file_path_resolved, "r", encoding="utf-8") as f:
            return json.load(f)

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


def _validate_path_in_reports_dir(file_path: Path) -> None:
    """
    验证路径在允许的 REPORTS_DIR 内，防止路径遍历

    Args:
        file_path: 要验证的文件路径

    Raises:
        HTTPException: 路径遍历检测
    """
    try:
        reports_dir_resolved = Path(ResearcherConfig.REPORTS_DIR).resolve()
        file_path_resolved = file_path.resolve()

        # 检查解析后的路径是否在 REPORTS_DIR 内
        file_path_resolved.relative_to(reports_dir_resolved)
    except ValueError:
        logger.warning(f"Path traversal attempt detected: {file_path}")
        raise HTTPException(status_code=403, detail="Path traversal detected")


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


def _get_report_store() -> Optional[Any]:
    """延迟导入 researcher_store，兼容测试中的 monkeypatch。"""
    try:
        return importlib.import_module("researcher_store")
    except ImportError:
        logger.error("researcher_store 不可用")
        return None


def _load_latest_report(date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    store = _get_report_store()
    if store is None:
        raise HTTPException(status_code=503, detail="researcher_store unavailable")
    return store.get_latest(date)


def _researcher_health_url() -> str:
    configured_url = os.getenv("RESEARCHER_SERVICE_URL", "").strip()
    if configured_url:
        return f"{configured_url.rstrip('/')}/health"

    ollama_url = str(ResearcherConfig.OLLAMA_URL).rstrip("/")
    parsed = urlparse(ollama_url)
    host = parsed.hostname or "192.168.31.187"
    scheme = parsed.scheme or "http"
    return f"{scheme}://{host}:8199/health"


def _get_resource_status() -> Dict[str, bool]:
    """返回 Alienware 可达性与 Ollama 可用性，避免硬编码口径。"""
    ollama_url = str(ResearcherConfig.OLLAMA_URL).rstrip("/")
    timeout = ResearcherConfig.HTTP_TIMEOUT_SHORT

    try:
        resp = httpx.get(_researcher_health_url(), timeout=timeout)
        alienware_reachable = resp.is_success
    except httpx.HTTPError as exc:
        logger.warning("Alienware reachability check failed: %s", exc)
        alienware_reachable = False

    ollama_available = False
    if alienware_reachable:
        try:
            resp = httpx.get(f"{ollama_url}/api/tags", timeout=timeout)
            ollama_available = resp.is_success
        except httpx.HTTPError as exc:
            logger.warning("Ollama availability check failed: %s", exc)

    return {
        "alienware_reachable": alienware_reachable,
        "ollama_available": ollama_available,
    }


@router.get("/report/latest")
async def get_latest_report(date: Optional[str] = Query(None, description="可选日期 YYYY-MM-DD")) -> Dict[str, Any]:
    """获取最新一期研究员报告（JSON 决策版）"""
    if date is not None and not _validate_path_component(date, "date"):
        raise HTTPException(status_code=400, detail="Invalid date format")

    latest_report = _load_latest_report(date)
    if latest_report is None:
        raise HTTPException(status_code=404, detail="No reports found")
    return latest_report


@router.get("/report/{date}")
async def get_reports_by_date(date: str) -> Dict[str, Any]:
    """获取指定日期的研究员报告列表"""
    # 安全修复：P0-1 - 验证日期格式，防止路径遍历
    if not _validate_path_component(date, "date"):
        raise HTTPException(status_code=400, detail="Invalid date format")

    date_dir = Path(ResearcherConfig.REPORTS_DIR) / date

    # 验证路径在允许的目录内
    _validate_path_in_reports_dir(date_dir)

    if not date_dir.exists():
        raise HTTPException(status_code=404, detail=f"No reports found for date {date}")

    segments = []
    for segment_file in date_dir.glob("*.json"):
        # 使用安全读取函数
        report = _safe_read_json_file(segment_file)
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
    # 安全修复：P0-1 - 验证日期和段名格式，防止路径遍历
    if not _validate_path_component(date, "date"):
        raise HTTPException(status_code=400, detail="Invalid date format")
    if not _validate_path_component(segment, "segment"):
        raise HTTPException(status_code=400, detail="Invalid segment format")

    report_path = Path(ResearcherConfig.REPORTS_DIR) / date / f"{segment}.json"

    # 验证路径在允许的目录内
    _validate_path_in_reports_dir(report_path)

    # 使用安全读取函数
    return _safe_read_json_file(report_path)


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """研究员子系统状态"""
    # 获取最新报告信息
    last_run = None
    try:
        latest_report = _load_latest_report()
        if latest_report is not None:
            last_run = {
                "report_id": latest_report["report_id"],
                "segment": latest_report["segment"],
                "generated_at": latest_report["generated_at"]
            }
    except HTTPException as exc:
        if exc.status_code == 503:
            raise

    return {
        "status": "running",
        "last_run": last_run,
        "next_schedule": {
            "盘前": "08:30",
            "午间": "11:35",
            "盘后": "15:20",
            "夜盘": "23:10"
        },
        "resource_status": _get_resource_status()
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
