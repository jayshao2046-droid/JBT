#!/usr/bin/env python3
"""研究员服务启动脚本 - Alienware 24x7 运行

职责：
1. 启动 FastAPI 服务（端口 8199）
2. 接收 Mini data 采集器回调
3. 定时触发研究员分析任务
4. 推送报告到 Studio decision
5. 提供报告读取和状态管理 API

部署位置：Alienware (192.168.31.223)
运行方式：Windows 任务计划 / 手动启动
"""

import os
import sys
import logging
import json
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("runtime/researcher/logs/server.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="JBT Researcher Service", version="1.0.0")

# 全局调度器和队列管理器实例
scheduler: Optional[ResearcherScheduler] = None
queue_manager: Optional[QueueManager] = None


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
    global scheduler, queue_manager
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


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    global scheduler
    if scheduler:
        await scheduler.close()
    logger.info("研究员服务已关闭")


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

    try:
        # 执行研究员任务
        result = await scheduler.execute_hourly(hour=hour)

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


@app.post("/callback")
async def data_collection_callback(request: CallbackRequest):
    """
    接收 Mini data 采集器回调

    当 Mini data 采集完成后，自动触发研究员分析
    """
    logger.info(
        f"[CALLBACK] 收到 Mini data 回调: "
        f"collector={request.collector}, "
        f"records={request.record_count}, "
        f"elapsed={request.elapsed_sec:.2f}s"
    )

    # 触发研究员分析
    hour = datetime.now().hour
    await trigger_research(hour=hour)

    return {
        "success": True,
        "message": "已触发研究员分析"
    }


@app.get("/reports/latest")
async def get_latest_report():
    """
    获取最新研究报告

    供 Studio decision 服务调用
    """
    global queue_manager

    if not queue_manager:
        raise HTTPException(status_code=500, detail="队列管理器未初始化")

    try:
        # 获取待读队列中的最新报告
        pending = queue_manager.get_pending(limit=1)
        if not pending:
            raise HTTPException(status_code=404, detail="无待读报告")

        report_record = pending[0]
        file_path = report_record["file_path"]

        # 读取报告文件
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"报告文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        logger.info(f"[API] 读取最新报告: {report_record['report_id']}")

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
    main()
