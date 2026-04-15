"""测试对话控制器"""
import pytest
from researcher.chat_controller import ChatController


def test_chat_controller_init():
    """测试对话控制器初始化"""
    controller = ChatController()
    assert controller is not None


def test_process_status_command():
    """测试状态查询指令"""
    controller = ChatController()

    result = controller.process_command("查询状态")

    assert result["success"] is True
    assert "运行" in result["message"]


def test_process_report_command():
    """测试报告查询指令"""
    controller = ChatController()

    result = controller.process_command("查看报告")

    assert result["success"] is True
    assert "报告" in result["message"]
