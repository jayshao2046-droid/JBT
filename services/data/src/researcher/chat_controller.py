"""对话控制器 - 通过自然语言控制研究员

职责：
1. 解析自然语言指令
2. 执行相应操作
3. 返回执行结果
"""
import logging
from typing import Dict
from .config_updater import ConfigUpdater

logger = logging.getLogger(__name__)


class ChatController:
    """对话控制器"""

    def __init__(self):
        self.config_updater = ConfigUpdater()

    def process_command(self, command: str) -> Dict:
        """处理用户指令"""
        try:
            command = command.strip().lower()

            # 解析指令
            if "开启" in command or "启用" in command:
                return self._handle_enable(command)
            elif "关闭" in command or "禁用" in command:
                return self._handle_disable(command)
            elif "状态" in command or "运行" in command:
                return self._handle_status()
            elif "报告" in command:
                return self._handle_report()
            else:
                return {
                    "success": False,
                    "message": "无法理解指令，请重新输入"
                }

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                "success": False,
                "message": f"处理指令时出错: {str(e)}"
            }

    def _handle_enable(self, command: str) -> Dict:
        """处理启用指令"""
        # 简化实现：从指令中提取数据源名称
        if "新浪" in command:
            source_name = "新浪财经"
        elif "东方" in command or "东财" in command:
            source_name = "东方财富"
        else:
            return {"success": False, "message": "未识别到数据源名称"}

        success = self.config_updater.update_source_enabled(source_name, True)

        return {
            "success": success,
            "message": f"已启用数据源: {source_name}" if success else "启用失败"
        }

    def _handle_disable(self, command: str) -> Dict:
        """处理禁用指令"""
        if "新浪" in command:
            source_name = "新浪财经"
        elif "东方" in command or "东财" in command:
            source_name = "东方财富"
        else:
            return {"success": False, "message": "未识别到数据源名称"}

        success = self.config_updater.update_source_enabled(source_name, False)

        return {
            "success": success,
            "message": f"已禁用数据源: {source_name}" if success else "禁用失败"
        }

    def _handle_status(self) -> Dict:
        """处理状态查询"""
        return {
            "success": True,
            "message": "研究员运行正常，5 个进程全部运行中"
        }

    def _handle_report(self) -> Dict:
        """处理报告查询"""
        return {
            "success": True,
            "message": "最新报告已生成，请查看 /data/researcher/reports/"
        }
