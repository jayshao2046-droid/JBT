"""
LLM 分析器 - 使用 qwen3:14b 分析数据

职责：
1. 从共享队列消费数据
2. 调用 Ollama qwen3:14b 进行分析
3. 结合历史上下文连贯写作
4. 输出分析结果到报告缓冲区
"""
import logging
import time
from datetime import datetime
import requests
import multiprocessing as mp
import json

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """LLM 分析器"""

    def __init__(self, queue: mp.Queue, stop_event: mp.Event):
        self.queue = queue
        self.stop_event = stop_event
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "qwen3:14b"

        # 报告缓冲区（简化：实际应使用共享内存或数据库）
        self.report_buffer = []

    def run(self):
        """主循环"""
        logger.info("LLMAnalyzer started")

        while not self.stop_event.is_set():
            try:
                # 从队列获取数据（超时1秒）
                try:
                    event = self.queue.get(timeout=1)
                except:
                    continue

                # 分析数据
                analysis = self._analyze_event(event)
                if analysis:
                    self.report_buffer.append(analysis)

                    # 缓冲区满了就清理旧数据
                    if len(self.report_buffer) > 1000:
                        self.report_buffer = self.report_buffer[-500:]

            except Exception as e:
                logger.error(f"LLMAnalyzer error: {e}", exc_info=True)
                time.sleep(1)

        logger.info("LLMAnalyzer stopped")

    def _analyze_event(self, event: dict) -> dict:
        """分析单个事件"""
        try:
            event_type = event.get("type")

            if event_type == "kline_alert":
                return self._analyze_kline_alert(event)
            elif event_type == "news":
                return self._analyze_news(event)
            elif event_type == "fundamental":
                return self._analyze_fundamental(event)
            else:
                return None

        except Exception as e:
            logger.error(f"Error analyzing event: {e}")
            return None

    def _analyze_kline_alert(self, event: dict) -> dict:
        """分析 K 线异常波动"""
        symbol = event.get("symbol")
        change_pct = event.get("change_pct")

        prompt = f"""
分析以下期货品种的异常波动：

品种：{symbol}
涨跌幅：{change_pct:.2f}%
时间：{event.get("timestamp")}

请简要分析：
1. 可能的原因
2. 后续走势预判
3. 风险提示

要求：50字以内，简洁明了。
"""

        analysis_text = self._call_ollama(prompt)

        return {
            "type": "kline_analysis",
            "symbol": symbol,
            "change_pct": change_pct,
            "analysis": analysis_text,
            "timestamp": datetime.now().isoformat()
        }

    def _analyze_news(self, event: dict) -> dict:
        """分析新闻"""
        title = event.get("title")

        prompt = f"""
分析以下期货新闻的影响：

标题：{title}

请简要分析：
1. 影响的品种
2. 利多还是利空
3. 影响程度（高/中/低）

要求：30字以内。
"""

        analysis_text = self._call_ollama(prompt)

        return {
            "type": "news_analysis",
            "title": title,
            "analysis": analysis_text,
            "timestamp": datetime.now().isoformat()
        }

    def _analyze_fundamental(self, event: dict) -> dict:
        """分析基本面数据"""
        source = event.get("source")
        data_type = event.get("data_type")

        return {
            "type": "fundamental_analysis",
            "source": source,
            "data_type": data_type,
            "analysis": f"基本面数据来自 {source}",
            "timestamp": datetime.now().isoformat()
        }

    def _call_ollama(self, prompt: str) -> str:
        """调用 Ollama API"""
        try:
            resp = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )

            if resp.status_code == 200:
                result = resp.json()
                return result.get("response", "")
            else:
                return "分析失败"

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return "分析失败"
