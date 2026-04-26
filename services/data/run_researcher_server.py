#!/usr/bin/env python3
"""研究员服务启动脚本 - Alienware 24x7 运行

职责：
1. 启动 FastAPI 服务（端口 8199）
2. 接收 Mini data 采集器回调
3. 定时触发研究员分析任务
4. 推送报告到 Studio decision
5. 提供报告读取和状态管理 API

部署位置：Alienware (192.168.31.187)
运行方式：Windows 任务计划 / 手动启动
"""

import os
import sys
import logging
import json
import asyncio
import atexit
import threading
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from typing import Optional, Dict

# 导入研究员模块
from services.data.src.researcher.scheduler import ResearcherScheduler
from services.data.src.researcher.config import ResearcherConfig
from services.data.src.researcher.queue_manager import QueueManager

# --- 日志设置：直接挂 handler，避免 QueueListener daemon 线程在 Windows 丢日志 ---
_log_dir = Path("runtime/researcher/logs")
_log_dir.mkdir(parents=True, exist_ok=True)

class _FlushFileHandler(logging.FileHandler):
    """每条日志写入后立即 flush + fsync"""
    def emit(self, record):
        super().emit(record)
        self.flush()
        try:
            os.fsync(self.stream.fileno())
        except (OSError, ValueError):
            pass

_file_handler = _FlushFileHandler(str(_log_dir / "server.log"), encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
_console_handler = logging.StreamHandler()  # 默认 stderr，避免 Start-Process 无 stdout
_console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(_file_handler)
root_logger.addHandler(_console_handler)

def _flush_all_logs():
    for h in root_logger.handlers:
        try:
            h.flush()
        except Exception:
            pass

atexit.register(_flush_all_logs)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="JBT Researcher Service", version="1.0.0")

# 全局调度器和队列管理器实例
scheduler: Optional[ResearcherScheduler] = None
queue_manager: Optional[QueueManager] = None
_continuous_thread: Optional[threading.Thread] = None
_continuous_running: bool = False

# 防止 /run 端点触发的 execute_hourly 并发重入
_hourly_lock = threading.Lock()

# 全量采集状态
_full_crawl_running = False
_full_crawl_last_result: dict = {}


class CallbackRequest(BaseModel):
    """Mini data 采集器回调请求"""
    source: str
    collector: str
    record_count: int
    elapsed_sec: float
    timestamp: str


class MarkReadRequest(BaseModel):
    """标记已读请求"""
    score: Optional[float] = None
    reasoning: Optional[str] = None
    model: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global scheduler, queue_manager, _continuous_task, _continuous_running
    logger.info("=" * 60)
    logger.info("JBT 研究员服务启动")
    logger.info(f"时间: {datetime.now()}")
    logger.info(f"端口: 8199")
    logger.info(f"Ollama: {ResearcherConfig.OLLAMA_URL}")
    logger.info(f"模型: {ResearcherConfig.OLLAMA_MODEL}")
    logger.info(f"Mini data API: {ResearcherConfig.DATA_API_URL}")
    logger.info(f"报告目录: {ResearcherConfig.REPORTS_DIR}")
    logger.info("=" * 60)

    # 确保必要目录存在
    ResearcherConfig.ensure_dirs()

    # 初始化队列管理器
    queue_dir = os.path.join(ResearcherConfig.REPORTS_DIR, ".queue")
    queue_manager = QueueManager(queue_dir)
    logger.info(f"队列管理器初始化: {queue_dir}")

    # 初始化调度器（传入队列管理器）
    scheduler = ResearcherScheduler(queue_manager=queue_manager)
    logger.info("研究员调度器初始化完成")

    # 启动 24 小时持续运行循环（独立线程 + 独立 event loop）
    _continuous_running = True
    _continuous_thread = threading.Thread(target=_continuous_loop_thread, daemon=True)
    _continuous_thread.start()
    logger.info("[LOOP] 24 小时持续研究循环已启动（独立线程）")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    global scheduler, _continuous_thread, _continuous_running
    _continuous_running = False
    if _continuous_thread and _continuous_thread.is_alive():
        _continuous_thread.join(timeout=10)
    if scheduler:
        await scheduler.close()
    logger.info("研究员服务已关闭")


def _continuous_loop_thread():
    """独立线程：流式循环 — 持续爬取+分析+推送，拥有自己的 event loop"""
    global scheduler, _continuous_running
    loop_count = 0
    logger.info("[LOOP] 流式研究循环开始（独立线程）")
    # 创建独立 event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        while _continuous_running:
            try:
                loop_count += 1
                logger.info(f"[LOOP] 流式周期 {loop_count} 开始")
                result = loop.run_until_complete(scheduler.execute_stream_cycle())
                elapsed = result.get("elapsed_seconds", 0)
                mode = result.get("mode", "?")
                new_art = result.get("new_articles", 0)
                kline = result.get("kline_reports", 0)
                today_total = result.get("today_total_articles", 0)
                logger.info(
                    f"[LOOP] 流式周期 {loop_count} 完成: "
                    f"mode={mode}, new_articles={new_art}, kline={kline}, "
                    f"today_total={today_total}, elapsed={elapsed:.1f}s"
                )
                _flush_all_logs()
                # 如果本轮无新内容，则等待 callback 等事件请求或 30 秒后再轮询
                if new_art == 0 and kline == 0:
                    wait_reason = scheduler.wait_for_stream_cycle_request(timeout_seconds=30) if scheduler else None
                    if wait_reason:
                        logger.info(f"[LOOP] 收到即时 stream 请求，提前开始下一轮: reason={wait_reason}")
            except Exception as e:
                logger.error(f"[LOOP] 流式周期 {loop_count} 异常: {e}", exc_info=True)
                wait_reason = scheduler.wait_for_stream_cycle_request(timeout_seconds=60) if scheduler else None
                if wait_reason:
                    logger.info(f"[LOOP] 异常后收到即时 stream 请求，提前重试: reason={wait_reason}")
    finally:
        loop.close()
    logger.info(f"[LOOP] 流式研究循环结束，共完成 {loop_count} 轮")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "researcher",
        "timestamp": datetime.now().isoformat(),
        "ollama_url": ResearcherConfig.OLLAMA_URL,
        "model": ResearcherConfig.OLLAMA_MODEL
    }


@app.post("/run")
async def trigger_research(hour: Optional[int] = None):
    """
    手动触发研究员分析

    Args:
        hour: 小时数（0-23），用于确定时段

    Returns:
        执行结果
    """
    global scheduler

    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    # 如果未指定 hour，使用当前小时
    if hour is None:
        hour = datetime.now().hour

    logger.info(f"[TRIGGER] 手动触发研究员分析: hour={hour}")

    # 防止并发重入：如果 execute_hourly 已在运行，直接返回
    if not _hourly_lock.acquire(blocking=False):
        logger.warning("[TRIGGER] execute_hourly 已在运行，跳过本次触发")
        return {"success": False, "message": "已有分析任务正在运行，请稍后再试", "hour": hour}

    try:
        # 执行研究员任务（run_in_executor + 独立 event loop 避免阻塞 FastAPI）
        loop = asyncio.get_event_loop()
        def _run_hourly(h):
            _loop = asyncio.new_event_loop()
            try:
                return _loop.run_until_complete(scheduler.execute_hourly(hour=h))
            finally:
                _loop.close()
        result = await loop.run_in_executor(None, _run_hourly, hour)

        return {
            "success": True,
            "hour": hour,
            "timestamp": datetime.now().isoformat(),
            "message": f"研究员分析已触发（hour={hour}）",
            "result": result
        }

    except Exception as e:
        logger.error(f"[TRIGGER] 执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")
    finally:
        _hourly_lock.release()


@app.post("/crawl/full")
async def trigger_full_crawl():
    """
    全量采集 — 后台异步触发，立即返回。
    通过 GET /crawl/status 查看进度和结果。
    """
    global scheduler, _full_crawl_running, _full_crawl_last_result

    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    if _full_crawl_running:
        return {"success": False, "message": "全量采集已在运行中，请稍后通过 /crawl/status 查询结果"}

    async def _do_full():
        global _full_crawl_running, _full_crawl_last_result
        _full_crawl_running = True
        try:
            logger.info("[CRAWL/FULL] 全量采集开始（force_all=True）")
            articles = await scheduler._crawl_stream_with_dedup(force_all=True)
            _full_crawl_last_result = {
                "status": "done",
                "total_new_articles": len(articles),
                "active_sources": list({a.get("source_id") for a in articles if a.get("source_id")}),
                "fail_counts": dict(scheduler._source_fail_count),
                "finished_at": datetime.now().isoformat(),
            }
            logger.info(f"[CRAWL/FULL] 完成: {len(articles)} 新文章, 失败源: {dict(scheduler._source_fail_count)}")
        except Exception as e:
            _full_crawl_last_result = {"status": "error", "error": str(e), "finished_at": datetime.now().isoformat()}
            logger.error(f"[CRAWL/FULL] 失败: {e}", exc_info=True)
        finally:
            _full_crawl_running = False

    asyncio.create_task(_do_full())
    return {
        "success": True,
        "message": "全量采集已在后台启动，通过 GET /crawl/status 查询结果",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/crawl/status")
async def crawl_source_status():
    """返回各采集源的连续失败计数及最近一次全量采集结果"""
    global scheduler, _full_crawl_running, _full_crawl_last_result
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")
    return {
        "full_crawl_running": _full_crawl_running,
        "full_crawl_last_result": _full_crawl_last_result,
        "fail_counts": dict(scheduler._source_fail_count),
        "notified_at": {k: v.isoformat() for k, v in scheduler._source_fail_notified_at.items()},
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/callback")
async def data_collection_callback(request: CallbackRequest):
    """
    接收 Mini data 采集器回调

    当 Mini data 采集完成后，请求一次即时 stream cycle。
    """
    global scheduler, _continuous_thread

    logger.info(
        f"[CALLBACK] 收到 Mini data 回调: "
        f"collector={request.collector}, "
        f"records={request.record_count}, "
        f"elapsed={request.elapsed_sec:.2f}s"
    )

    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    if not _continuous_thread or not _continuous_thread.is_alive():
        raise HTTPException(status_code=503, detail="stream 主链未运行")

    reason = f"callback:{request.source}:{request.collector}"
    scheduler.request_stream_cycle(reason=reason)
    logger.info(f"[CALLBACK] 已请求即时 stream cycle: reason={reason}")

    return {
        "success": True,
        "message": "已请求即时 stream cycle",
        "trigger": "stream_cycle",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/reports/latest")
async def get_latest_report():
    """
    获取最新研究报告（latest 语义：最新且可读的报告）

    供 Studio decision 服务调用。
    修复：原实现用 get_pending(limit=1) 返回 FIFO 最旧条目，
    导致 stale 旧文件阻塞后续所有报告。
    现改为：取全量 pending，按文件路径倒序（路径含日期目录），
    跳过文件不存在的 stale 记录，返回最新可读报告。
    """
    global queue_manager

    if not queue_manager:
        raise HTTPException(status_code=500, detail="队列管理器未初始化")

    try:
        # 取全量 pending（上限 200 条），按文件路径倒序找最新可读报告
        pending = queue_manager.get_pending(limit=200)
        if not pending:
            raise HTTPException(status_code=404, detail="无待读报告")

        # 按 file_path 降序排列（路径含 YYYY-MM-DD/HH-MM.json，字典序即时间序）
        pending_sorted = sorted(pending, key=lambda r: r.get("file_path", ""), reverse=True)

        report_record = None
        file_path = None
        for record in pending_sorted:
            fp = record.get("file_path", "")
            if fp and os.path.exists(fp):
                report_record = record
                file_path = fp
                break

        if not report_record:
            logger.warning("[API] pending 队列中所有报告文件均不存在（stale），无可读报告")
            raise HTTPException(status_code=404, detail="无可读待读报告（所有记录均为 stale）")

        with open(file_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        logger.info(f"[API] 读取最新报告: {report_record['report_id']} ({file_path})")

        return report_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 读取报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"读取失败: {str(e)}")


@app.post("/reports/{report_id}/mark_read")
async def mark_report_read(report_id: str, request: MarkReadRequest):
    """
    标记报告为已读

    供 Studio decision 评级完成后调用
    """
    global queue_manager

    if not queue_manager:
        raise HTTPException(status_code=500, detail="队列管理器未初始化")

    try:
        # 标记为处理中（如果还在 pending）
        status = queue_manager.get_status(report_id)
        if status == "pending":
            queue_manager.mark_processing(report_id)

        # 标记为已完成
        result = {
            "score": request.score,
            "reasoning": request.reasoning,
            "model": request.model,
            "marked_at": datetime.now().isoformat()
        }
        success = queue_manager.mark_completed(report_id, result)

        if not success:
            raise HTTPException(status_code=404, detail=f"报告不存在或状态错误: {report_id}")

        logger.info(
            f"[API] 标记已读: {report_id}, "
            f"score={request.score}, model={request.model}"
        )

        return {
            "success": True,
            "report_id": report_id,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 标记失败: {report_id}, {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"标记失败: {str(e)}")


@app.get("/queue/status")
async def get_queue_status():
    """
    获取队列状态

    返回待读、处理中、已完成的报告数量
    """
    global queue_manager

    if not queue_manager:
        raise HTTPException(status_code=500, detail="队列管理器未初始化")

    try:
        pending = queue_manager.get_pending(limit=1000)
        processing = queue_manager.get_processing()

        return {
            "pending_count": len(pending),
            "processing_count": len(processing),
            "pending_reports": [
                {
                    "report_id": r["report_id"],
                    "file_path": r["file_path"],
                    "added_at": r["added_at"]
                }
                for r in pending[:10]  # 只返回前 10 个
            ],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"[API] 获取队列状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


def main():
    """主函数"""
    # 确保运行目录正确
    os.chdir(project_root)

    # 启动服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8199,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    # Windows 上必须使用 ProactorEventLoop 才能支持子进程和 asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    main()
