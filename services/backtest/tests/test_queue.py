"""测试任务队列管理器"""
import pytest
import asyncio
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.queue.manager import QueueManager, BacktestTask, TaskStatus


@pytest.fixture
def queue_manager():
    """创建队列管理器实例"""
    return QueueManager(max_concurrent=2)


@pytest.mark.asyncio
async def test_submit_task(queue_manager):
    """测试提交任务"""
    task_id = await queue_manager.submit_task(
        strategy_id="test_strategy",
        config={"param1": 10},
        priority=0
    )

    assert task_id is not None
    assert task_id in queue_manager.tasks

    task = queue_manager.get_task(task_id)
    assert task.strategy_id == "test_strategy"
    assert task.config["param1"] == 10
    assert task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]


@pytest.mark.asyncio
async def test_task_priority(queue_manager):
    """测试任务优先级"""
    # 提交低优先级任务
    task_id_low = await queue_manager.submit_task(
        strategy_id="low_priority",
        config={},
        priority=0
    )

    # 提交高优先级任务
    task_id_high = await queue_manager.submit_task(
        strategy_id="high_priority",
        config={},
        priority=10
    )

    # 等待一小段时间让任务开始执行
    await asyncio.sleep(0.1)

    # 高优先级任务应该先执行或在队列前面
    task_low = queue_manager.get_task(task_id_low)
    task_high = queue_manager.get_task(task_id_high)

    # 如果两个任务都在等待，高优先级应该在前面
    if task_low.status == TaskStatus.PENDING and task_high.status == TaskStatus.PENDING:
        assert queue_manager.pending_queue.index(task_id_high) < queue_manager.pending_queue.index(task_id_low)


@pytest.mark.asyncio
async def test_cancel_pending_task(queue_manager):
    """测试取消待执行任务"""
    # 提交多个任务以填满队列
    task_ids = []
    for i in range(5):
        task_id = await queue_manager.submit_task(
            strategy_id=f"strategy_{i}",
            config={},
            priority=0
        )
        task_ids.append(task_id)

    # 取消一个待执行的任务
    pending_task_id = None
    for tid in task_ids:
        task = queue_manager.get_task(tid)
        if task.status == TaskStatus.PENDING:
            pending_task_id = tid
            break

    if pending_task_id:
        success = await queue_manager.cancel_task(pending_task_id)
        assert success is True

        task = queue_manager.get_task(pending_task_id)
        assert task.status == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_running_task(queue_manager):
    """测试取消正在运行的任务"""
    task_id = await queue_manager.submit_task(
        strategy_id="test_strategy",
        config={},
        priority=0
    )

    # 等待任务开始运行
    await asyncio.sleep(0.1)

    task = queue_manager.get_task(task_id)
    if task.status == TaskStatus.RUNNING:
        success = await queue_manager.cancel_task(task_id)
        assert success is True

        # 等待取消完成
        await asyncio.sleep(0.1)

        task = queue_manager.get_task(task_id)
        assert task.status == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_list_tasks(queue_manager):
    """测试列出任务"""
    # 提交多个任务
    for i in range(3):
        await queue_manager.submit_task(
            strategy_id=f"strategy_{i}",
            config={},
            priority=0
        )

    # 列出所有任务
    all_tasks = queue_manager.list_tasks()
    assert len(all_tasks) >= 3

    # 按状态过滤
    pending_tasks = queue_manager.list_tasks(status=TaskStatus.PENDING)
    assert all(t.status == TaskStatus.PENDING for t in pending_tasks)


@pytest.mark.asyncio
async def test_queue_status(queue_manager):
    """测试队列状态"""
    # 提交任务
    await queue_manager.submit_task("strategy_1", {}, priority=0)
    await queue_manager.submit_task("strategy_2", {}, priority=0)

    status = queue_manager.get_queue_status()

    assert "total_tasks" in status
    assert "pending" in status
    assert "running" in status
    assert "completed" in status
    assert "failed" in status
    assert "cancelled" in status
    assert "max_concurrent" in status

    assert status["max_concurrent"] == 2
    assert status["total_tasks"] >= 2


@pytest.mark.asyncio
async def test_max_concurrent_limit(queue_manager):
    """测试最大并发限制"""
    # 提交多个任务
    task_ids = []
    for i in range(5):
        task_id = await queue_manager.submit_task(
            strategy_id=f"strategy_{i}",
            config={},
            priority=0
        )
        task_ids.append(task_id)

    # 等待任务开始执行
    await asyncio.sleep(0.2)

    # 检查运行中的任务数量不超过最大并发数
    running_count = len([
        t for t in queue_manager.tasks.values()
        if t.status == TaskStatus.RUNNING
    ])

    assert running_count <= queue_manager.max_concurrent


@pytest.mark.asyncio
async def test_task_completion(queue_manager):
    """测试任务完成"""
    task_id = await queue_manager.submit_task(
        strategy_id="test_strategy",
        config={},
        priority=0
    )

    # 等待任务完成（模拟任务需要 5 秒）
    await asyncio.sleep(6)

    task = queue_manager.get_task(task_id)
    assert task.status == TaskStatus.COMPLETED
    assert task.result is not None
    assert task.completed_at is not None


@pytest.mark.asyncio
async def test_clear_completed(queue_manager):
    """测试清理已完成任务"""
    # 提交并等待任务完成
    task_id = await queue_manager.submit_task(
        strategy_id="test_strategy",
        config={},
        priority=0
    )

    await asyncio.sleep(6)

    # 清理已完成的任务（0 小时前，即立即清理）
    await queue_manager.clear_completed(older_than_hours=0)

    # 任务应该被清理
    task = queue_manager.get_task(task_id)
    assert task is None


@pytest.mark.asyncio
async def test_task_progress(queue_manager):
    """测试任务进度"""
    task_id = await queue_manager.submit_task(
        strategy_id="test_strategy",
        config={},
        priority=0
    )

    # 等待任务开始并运行一段时间
    await asyncio.sleep(2)

    task = queue_manager.get_task(task_id)
    if task.status == TaskStatus.RUNNING:
        # 进度应该在 0 到 1 之间
        assert 0 <= task.progress <= 1
