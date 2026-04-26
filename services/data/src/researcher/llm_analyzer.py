"""
LLM 分析器 - 使用 qwen3:14b-q4_K_M 分析数据

职责：
1. 从共享队列消费数据
2. 调用 Ollama qwen3:14b-q4_K_M 进行分析
3. 结合历史上下文连贯写作
4. 输出分析结果到报告缓冲区

F1（2026-04-24）参数收紧：
- 关闭 <think> 长推理（prompt 头部注入 /no_think）
- 固定 num_predict / num_ctx / keep_alive
- 单条 timeout 收紧到 OLLAMA_NEWS_TIMEOUT
- 若上游已通过 news_prefilter 打分（_prefilter_score < 阈值），直接跳过
"""
import logging
import time
import queue
from datetime import datetime
import requests
import multiprocessing as mp
import json

from .config import ResearcherConfig

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """LLM 分析器"""

    def __init__(self, queue: mp.Queue, stop_event: mp.Event):
        self.queue = queue
        self.stop_event = stop_event
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = ResearcherConfig.OLLAMA_MODEL

        # 报告缓冲区（简化：实际应使用共享内存或数据库）
        self.report_buffer = []

    def run(self):
        """主循环"""
        logger.info("LLMAnalyzer started")

        while not self.stop_event.is_set():
            try:
                # 从队列获取数据（超时1秒）
                # 安全修复：P0-6 - 明确捕获预期异常类型
                try:
                    event = self.queue.get(timeout=1)
                except queue.Empty:
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
            # F1：若上游 prefilter 已判为低分，跳过深分析
            score = event.get("_prefilter_score")
            if score is not None and score < ResearcherConfig.OLLAMA_PREFILTER_THRESHOLD:
                return None

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
        """调用 Ollama API（F1 收紧版）"""
        try:
            tightened_prompt = "/no_think\n" + prompt if "/no_think" not in prompt[:32] else prompt
            resp = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": tightened_prompt,
                    "stream": False,
                    "keep_alive": ResearcherConfig.OLLAMA_KEEP_ALIVE,
                    "options": {
                        "temperature": ResearcherConfig.OLLAMA_TEMPERATURE,
                        "num_ctx": 4096,
                        "num_predict": ResearcherConfig.OLLAMA_NUM_PREDICT,
                    },
                },
                timeout=ResearcherConfig.OLLAMA_NEWS_TIMEOUT,
            )

            if resp.status_code == 200:
                result = resp.json()
                text = result.get("response", "")
                if "<think>" in text and "</think>" in text:
                    text = text[text.index("</think>") + len("</think>"):]
                return text.strip()
            else:
                return "分析失败"

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return "分析失败"
