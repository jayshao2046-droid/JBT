"""
测试股票池管理器 (CB4)
"""
import pytest
from src.research.stock_pool import StockPool


def test_initial_pool_empty():
    """测试初始股票池为空"""
    pool = StockPool()
    assert pool.size() == 0
    assert pool.get_pool() == []


def test_add_symbol_success():
    """测试成功添加股票"""
    pool = StockPool()
    result = pool.add("600000.SH")
    assert result is True
    assert pool.size() == 1
    assert "600000.SH" in pool.get_pool()


def test_add_same_symbol_twice_returns_false():
    """测试重复添加同一股票返回 False"""
    pool = StockPool()
    pool.add("600000.SH")
    result = pool.add("600000.SH")
    assert result is False
    assert pool.size() == 1


def test_remove_existing_symbol():
    """测试移除存在的股票"""
    pool = StockPool()
    pool.add("600000.SH")
    result = pool.remove("600000.SH")
    assert result is True
    assert pool.size() == 0


def test_remove_nonexistent_returns_false():
    """测试移除不存在的股票返回 False"""
    pool = StockPool()
    result = pool.remove("600000.SH")
    assert result is False


def test_pool_size_limit():
    """测试股票池大小限制"""
    pool = StockPool(max_size=3)
    assert pool.add("600000.SH") is True
    assert pool.add("600001.SH") is True
    assert pool.add("600002.SH") is True
    # 第4个应该被拒绝
    assert pool.add("600003.SH") is False
    assert pool.size() == 3


def test_rotate_add_and_remove():
    """测试轮换操作"""
    pool = StockPool()
    pool.add("600000.SH")
    pool.add("600001.SH")

    result = pool.rotate(
        to_add=["600002.SH", "600003.SH"],
        to_remove=["600000.SH"]
    )

    assert result["removed_count"] == 1
    assert result["added_count"] == 2
    assert result["current_size"] == 3
    assert "600000.SH" not in pool.get_pool()
    assert "600002.SH" in pool.get_pool()
    assert "600003.SH" in pool.get_pool()


def test_rotate_exceeds_max_rejected():
    """测试轮换超出最大容量时被拒绝"""
    pool = StockPool(max_size=3)
    pool.add("600000.SH")
    pool.add("600001.SH")
    pool.add("600002.SH")

    result = pool.rotate(
        to_add=["600003.SH", "600004.SH"],
        to_remove=[]
    )

    # 已满，无法添加
    assert result["added_count"] == 0
    assert len(result["failed_add"]) == 2
    assert pool.size() == 3


def test_contains():
    """测试 contains 方法"""
    pool = StockPool()
    pool.add("600000.SH")
    assert pool.contains("600000.SH") is True
    assert pool.contains("600001.SH") is False


def test_to_dict_structure():
    """测试 to_dict 返回结构"""
    pool = StockPool()
    pool.add("600000.SH")

    data = pool.to_dict()
    assert "pool_id" in data
    assert "symbols" in data
    assert "max_size" in data
    assert "updated_at" in data
    assert data["symbols"] == ["600000.SH"]
    assert data["max_size"] == 30
    assert data["pool_id"].startswith("pool-")
