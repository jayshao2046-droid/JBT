"""
多进程管理器 - 管理研究员的 5 个进程

职责：
1. 启动/停止 5 个进程
2. 监控进程健康状态
3. 进程崩溃自动重启
4. 优雅关闭
"""
import logging
import multiprocessing as mp
import signal
import sys
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ProcessManager:
    """多进程管理器"""

    def __init__(self):
        self.processes: Dict[str, mp.Process] = {}
        self.should_stop = mp.Event()
        self.shared_queue = mp.Queue(maxsize=1000)

    def start_all(self):
        """启动所有进程"""
        from .kline_monitor import KlineMonitor
        from .news_crawler import NewsCrawler
        from .fundamental_crawler import FundamentalCrawler
        from .llm_analyzer import LLMAnalyzer
        from .report_generator import ReportGenerator

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 启动 5 个进程
        self.processes["kline_monitor"] = mp.Process(
            target=self._run_kline_monitor,
            name="KlineMonitor",
            daemon=False
        )

        self.processes["news_crawler"] = mp.Process(
            target=self._run_news_crawler,
            name="NewsCrawler",
            daemon=False
        )

        self.processes["fundamental_crawler"] = mp.Process(
            target=self._run_fundamental_crawler,
            name="FundamentalCrawler",
            daemon=False
        )

        self.processes["llm_analyzer"] = mp.Process(
            target=self._run_llm_analyzer,
            name="LLMAnalyzer",
            daemon=False
        )

        self.processes["report_generator"] = mp.Process(
            target=self._run_report_generator,
            name="ReportGenerator",
            daemon=False
        )

        # 启动所有进程
        for name, process in self.processes.items():
            process.start()
            logger.info(f"Started process: {name} (PID: {process.pid})")

        logger.info("All processes started successfully")

    def _run_kline_monitor(self):
        """运行 K 线监控器"""
        from .kline_monitor import KlineMonitor
        monitor = KlineMonitor(self.shared_queue, self.should_stop)
        monitor.run()

    def _run_news_crawler(self):
        """运行新闻爬虫"""
        from .news_crawler import NewsCrawler
        crawler = NewsCrawler(self.shared_queue, self.should_stop)
        crawler.run()

    def _run_fundamental_crawler(self):
        """运行基本面爬虫"""
        from .fundamental_crawler import FundamentalCrawler
        crawler = FundamentalCrawler(self.shared_queue, self.should_stop)
        crawler.run()

    def _run_llm_analyzer(self):
        """运行 LLM 分析器"""
        from .llm_analyzer import LLMAnalyzer
        analyzer = LLMAnalyzer(self.shared_queue, self.should_stop)
        analyzer.run()

    def _run_report_generator(self):
        """运行报告生成器"""
        from .report_generator import ReportGenerator
        generator = ReportGenerator(self.should_stop)
        generator.run()

    def monitor_health(self):
        """监控进程健康状态，崩溃自动重启"""
        while not self.should_stop.is_set():
            for name, process in list(self.processes.items()):
                if not process.is_alive():
                    logger.warning(f"Process {name} died, restarting...")
                    # 重启进程
                    if name == "kline_monitor":
                        new_process = mp.Process(target=self._run_kline_monitor, name="KlineMonitor")
                    elif name == "news_crawler":
                        new_process = mp.Process(target=self._run_news_crawler, name="NewsCrawler")
                    elif name == "fundamental_crawler":
                        new_process = mp.Process(target=self._run_fundamental_crawler, name="FundamentalCrawler")
                    elif name == "llm_analyzer":
                        new_process = mp.Process(target=self._run_llm_analyzer, name="LLMAnalyzer")
                    elif name == "report_generator":
                        new_process = mp.Process(target=self._run_report_generator, name="ReportGenerator")
                    else:
                        continue

                    new_process.start()
                    self.processes[name] = new_process
                    logger.info(f"Restarted process: {name} (PID: {new_process.pid})")

            time.sleep(10)  # 每 10 秒检查一次

    def stop_all(self):
        """停止所有进程"""
        logger.info("Stopping all processes...")
        self.should_stop.set()

        # 等待所有进程优雅退出
        for name, process in self.processes.items():
            process.join(timeout=10)
            if process.is_alive():
                logger.warning(f"Process {name} did not stop gracefully, terminating...")
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    logger.error(f"Process {name} did not terminate, killing...")
                    process.kill()

        logger.info("All processes stopped")

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"Received signal {signum}, stopping...")
        self.stop_all()
        sys.exit(0)


def main():
    """主入口"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    manager = ProcessManager()
    manager.start_all()

    try:
        manager.monitor_health()
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, stopping...")
    finally:
        manager.stop_all()


if __name__ == "__main__":
    main()
