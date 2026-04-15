"""每日运行统计追踪器 — 记录启动次数、研报数量与内容字节数

日志文件：runtime/researcher/logs/daily_stats_YYYY-MM-DD.json

结构示例：
{
  "date": "2026-04-15",
  "startup_count": 2,
  "reports_generated": 8,
  "reports_failed": 1,
  "total_content_bytes": 524288,
  "hourly": [
    {
      "hour": 8,
      "report_id": "RPT-20260415-08:00-001",
      "bytes": 65536,
      "elapsed_s": 58.1,
      "success": true,
      "decision_confidence": 0.72,
      "decision_confidence_reason": "trend_alignment=0.80, news_relevance=0.60, cross_consistency=0.75",
      "decision_reviewed_at": "2026-04-15T09:05:12"
    }
  ],
  "last_updated": "2026-04-15T14:00:05"
}

置信度评分标准（三维加权，Σweight=1.0）：
  news_relevance   (权重 0.30) — 爬取文章中含品种/上下游关键词的比例
  trend_alignment  (权重 0.40) — qwen3 趋势判断与 K 线技术指标（MA/RSI/ATR）的吻合度
  cross_consistency(权重 0.30) — 同板块/上下游品种间逻辑一致性

  综合置信度 = Σ(dimension × weight)
  ≥ 0.65 → 可直接采信
  0.40~0.64 → 人工复核
  < 0.40 → 建议忽略
"""

import json
import os
import threading
from datetime import datetime
from typing import Dict, Any, Optional


class DailyStatsTracker:
    """线程安全的每日运行统计，写入 daily_stats_YYYY-MM-DD.json"""

    _lock = threading.Lock()

    def __init__(self, logs_dir: str):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)

    # ── 内部 读/写 ────────────────────────────────────────────────────────

    def _stats_path(self, date: Optional[str] = None) -> str:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.logs_dir, f"daily_stats_{date}.json")

    def _load(self, date: Optional[str] = None) -> Dict[str, Any]:
        path = self._stats_path(date)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        today = date or datetime.now().strftime("%Y-%m-%d")
        return {
            "date": today,
            "startup_count": 0,
            "reports_generated": 0,
            "reports_failed": 0,
            "total_content_bytes": 0,
            "hourly": [],
            "last_updated": None,
        }

    def _save(self, data: Dict[str, Any]) -> None:
        """P1-6 修复：使用原子写入防止竞态条件"""
        data["last_updated"] = datetime.now().isoformat()
        path = self._stats_path(data["date"])

        # 原子写入：先写临时文件，再重命名
        temp_path = path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # 原子操作：rename 在 POSIX 系统上是原子的
            os.replace(temp_path, path)
        except Exception:
            # 清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise

    # ── 公开 API ──────────────────────────────────────────────────────────

    def record_startup(self) -> None:
        """服务进程启动时调用，累加当日启动次数"""
        with self._lock:
            data = self._load()
            data["startup_count"] += 1
            self._save(data)

    def record_report(
        self,
        hour: int,
        report_id: str,
        json_path: str,
        elapsed_s: float,
        success: bool,
    ) -> None:
        """每次研报生成（成功或失败）后调用"""
        with self._lock:
            date = datetime.now().strftime("%Y-%m-%d")
            data = self._load(date)

            bytes_written = 0
            if success and json_path and os.path.exists(json_path):
                try:
                    bytes_written = os.path.getsize(json_path)
                except OSError:
                    pass

            if success:
                data["reports_generated"] += 1
                data["total_content_bytes"] += bytes_written
            else:
                data["reports_failed"] += 1

            data["hourly"].append({
                "hour": hour,
                "report_id": report_id,
                "bytes": bytes_written,
                "elapsed_s": round(elapsed_s, 1),
                "success": success,
                "decision_confidence": None,
                "decision_confidence_reason": None,
                "decision_reviewed_at": None,
            })
            self._save(data)

    def record_decision_review(
        self,
        report_id: str,
        confidence: float,
        reason: str = "",
    ) -> bool:
        """
        决策端评分回写，按 report_id 更新对应日期的 hourly 条目。

        confidence 计算方式（由决策端按下面标准自行计算后传入）：
          news_relevance   * 0.30
          trend_alignment  * 0.40
          cross_consistency* 0.30
          综合 = Σ(维度得分 × 权重)

        返回：是否找到并更新了对应条目
        """
        with self._lock:
            # 从 report_id 解析日期: RPT-20260415-... → 2026-04-15
            try:
                raw = report_id.split("-")[1]  # "20260415"
                date = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
            except (IndexError, ValueError):
                date = datetime.now().strftime("%Y-%m-%d")

            data = self._load(date)
            found = False
            for entry in data["hourly"]:
                if entry.get("report_id") == report_id:
                    entry["decision_confidence"] = round(float(confidence), 4)
                    entry["decision_confidence_reason"] = reason
                    entry["decision_reviewed_at"] = datetime.now().isoformat()
                    found = True
                    break
            if found:
                self._save(data)
            return found

    def get_today(self) -> Dict[str, Any]:
        """获取当日统计快照（只读）"""
        with self._lock:
            return dict(self._load())
