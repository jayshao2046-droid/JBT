"""Heartbeat writer for JBT data service.

Migrated from Mini crontab: `* * * * * touch ~/.mini_heartbeat`
Now runs as a background thread within the data service process.
Includes 2-hour device health report push to Feishu.
"""

from __future__ import annotations

import os
import time
import threading
from datetime import datetime
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("data.heartbeat")

_DEFAULT_HEARTBEAT_FILE = Path.home() / ".jbt_data_heartbeat"
_DEFAULT_INTERVAL_SEC = 60
_HEALTH_REPORT_INTERVAL_SEC = 2 * 3600  # 2 hours


class HeartbeatWriter:
    """Writes a heartbeat timestamp file at fixed intervals."""

    def __init__(
        self,
        *,
        heartbeat_file: Path | None = None,
        interval_sec: int = _DEFAULT_INTERVAL_SEC,
    ) -> None:
        self._file = heartbeat_file or _DEFAULT_HEARTBEAT_FILE
        self._interval = interval_sec
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start heartbeat writer in a daemon thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("heartbeat already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="heartbeat-writer")
        self._thread.start()
        logger.info("heartbeat started: file=%s interval=%ds", self._file, self._interval)

    def stop(self) -> None:
        """Stop the heartbeat writer."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("heartbeat stopped")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._file.write_text(datetime.now().isoformat(), encoding="utf-8")
            except Exception as exc:
                logger.error("heartbeat write failed: %s", exc)
            self._stop_event.wait(timeout=self._interval)

    def is_alive(self, stale_seconds: int = 120) -> bool:
        """Check if the heartbeat file was updated within stale_seconds."""
        if not self._file.exists():
            return False
        try:
            age = time.time() - self._file.stat().st_mtime
            return age < stale_seconds
        except OSError:
            return False


class DeviceHealthReporter:
    """每 2 小时推送一次设备健康报告到飞书。"""

    def __init__(self, *, interval_sec: int = _HEALTH_REPORT_INTERVAL_SEC) -> None:
        self._interval = interval_sec
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.warning("health reporter already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="health-reporter")
        self._thread.start()
        logger.info("device health reporter started: interval=%ds", self._interval)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("health reporter stopped")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._push_report()
            except Exception as exc:
                logger.error("health report push failed: %s", exc)
            self._stop_event.wait(timeout=self._interval)

    def _push_report(self) -> None:
        """采集本机指标并推送飞书设备健康卡片。"""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not available, skipping health report")
            return

        cpu_pct = psutil.cpu_percent(interval=1)
        mem_pct = psutil.virtual_memory().percent
        disk_pct = psutil.disk_usage("/").percent

        # 进程状态 — 通过 ps aux 检测 JBT 进程（与 job_heartbeat 对齐）
        import subprocess
        procs: list[dict] = []
        try:
            ps_out = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=10,
            ).stdout
            for label, keyword in [
                ("数据采集调度", "data_scheduler"),
                ("数据 API",     "src.main"),
            ]:
                procs.append({"label": label, "ok": keyword in ps_out, "uptime": ""})
        except Exception as e:
            # P2-1 修复：记录异常详情
            logger.warning(f"Failed to check process status: {e}")

        # 网络延迟
        latency_ms = 0
        try:
            import socket
            t0 = time.time()
            s = socket.create_connection(("open.feishu.cn", 443), timeout=5)
            s.close()
            latency_ms = int((time.time() - t0) * 1000)
        except (socket.timeout, socket.error, OSError) as e:
            # P2-1 修复：记录网络错误类型
            logger.debug(f"Network latency check failed: {e}")
            latency_ms = -1
        except Exception as e:
            logger.warning(f"Unexpected error in latency check: {e}")
            latency_ms = -1

        webhook = (
            os.environ.get("FEISHU_ALERT_WEBHOOK_URL")
            or os.environ.get("FEISHU_WEBHOOK_URL")
            or os.environ.get("FEISHU_NEWS_WEBHOOK_URL")
            or os.environ.get("FEISHU_TRADING_WEBHOOK_URL")
            or ""
        )
        if not webhook:
            logger.warning("no webhook, skipping health report")
            return

        try:
            from src.notify import card_templates as ct
            from src.notify.feishu import FeishuSender

            card = ct.device_health_card(
                cpu_pct=cpu_pct,
                mem_pct=mem_pct,
                disk_pct=disk_pct,
                processes=procs,
                net_latency_ms=float(latency_ms),
            )
            sender = FeishuSender()
            sender.send_card(webhook, card)
            logger.info("device health report pushed: cpu=%.0f%% mem=%.0f%% disk=%.0f%%",
                        cpu_pct, mem_pct, disk_pct)
        except Exception as exc:
            logger.error("failed to push health report: %s", exc)
