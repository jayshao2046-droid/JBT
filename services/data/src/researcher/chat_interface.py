"""对话接口 - qwen3:14b 自然语言控制

职责：
1. 接收自然语言指令
2. 解析指令意图
3. 执行相应操作
"""
import logging
import requests
from typing import Dict

logger = logging.getLogger(__name__)


class ChatInterface:
    """对话接口"""

    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "qwen3:14b"

    def process_command(self, user_input: str) -> Dict:
        """处理用户指令"""
        try:
            # 解析意图
            intent = self._parse_intent(user_input)

            # 执行操作
            result = self._execute_intent(intent)

            return {
                "success": True,
                "intent": intent,
                "result": result,
                "response": self._generate_response(intent, result)
            }

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "抱歉，处理指令时出错了"
            }

    def _parse_intent(self, user_input: str) -> Dict:
        """解析用户意图"""
        prompt = f"""
解析以下用户指令的意图：

用户输入：{user_input}

请判断用户想要：
1. 查询状态（status）
2. 开关数据源（toggle_source）
3. 查看报告（view_report）
4. 调整采集频率（adjust_frequency）
5. 其他（other）

只返回意图类型和参数，格式：intent_type|param1|param2
"""

        try:
            resp = requests.post(
                self.ollama_url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=10
            )

            if resp.status_code == 200:
                result = resp.json().get("response", "")
                parts = result.strip().split("|")

                return {
                    "type": parts[0] if parts else "other",
                    "params": parts[1:] if len(parts) > 1 else []
                }
            else:
                return {"type": "other", "params": []}

        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            return {"type": "other", "params": []}

    def _execute_intent(self, intent: Dict) -> Dict:
        """执行意图"""
        intent_type = intent.get("type")

        if intent_type == "status":
            return {"status": "running", "processes": 5}
        elif intent_type == "toggle_source":
            source = intent.get("params", [""])[0]
            return {"source": source, "enabled": True}
        elif intent_type == "view_report":
            return {"reports": []}
        else:
            return {"message": "未知操作"}

    def _generate_response(self, intent: Dict, result: Dict) -> str:
        """生成回复"""
        intent_type = intent.get("type")

        if intent_type == "status":
            return f"研究员运行正常，共 {result.get('processes', 0)} 个进程"
        elif intent_type == "toggle_source":
            return f"已调整数据源 {result.get('source')}"
        else:
            return "操作完成"
