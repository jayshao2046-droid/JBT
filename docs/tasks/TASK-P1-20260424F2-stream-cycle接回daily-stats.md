# TASK-P1-20260424F2 — stream cycle 接回 daily_stats 埋点

## 任务类型
- P1 标准流程
- 服务归属：services/data
- 母任务（评估溯源）：2026-04-24 Atlas researcher 24h 只读评估
- 当前状态：待项目架构师预审 → 待 Jay.S 文件级 Token 签发
- 执行设备：MacBook 改代码 → rsync 同步 Alienware → 重启 researcher 服务

## 根因
`execute_stream_cycle` 是现役主链（由 `_continuous_loop_thread` 持续调用），但 `record_report` 只挂在废弃的 `execute_hourly` 内：
- `scheduler.py` L219 / L241：`record_report` 调用仅在 `execute_hourly` 内
- `execute_stream_cycle`（L1112）：完整跑完四个阶段后直接 return，**从不写入 daily_stats**
- 结果：`daily_stats_YYYY-MM-DD.json` 整日 `reports_generated=0`，评估盲区

## 改动范围（极小）
`execute_stream_cycle` 尾部（阶段4 邮件钩子结束、return 之前）增加一段统计埋点：

```python
# ── 统计埋点：接回 daily_stats ──
try:
    report_id_for_stats = (
        f"STREAM-{today}-{now.strftime('%H%M%S')}"
    )
    content_bytes = sum(
        len(json.dumps(r, ensure_ascii=False).encode())
        for r in analyzed
    )
    self.reporter.stats_tracker.record_report(
        hour=now.hour,
        report_id=report_id_for_stats,
        json_path="",          # stream cycle 无单一 json 路径
        elapsed_s=elapsed,
        success=(len(errors) == 0),
        content_bytes=content_bytes,
    )
except Exception as _stats_exc:
    logger.debug("[STREAM] daily_stats 写入失败(非阻断): %s", _stats_exc)
```

**关键约束**：
1. 用 `try/except` 包裹，写入失败不阻断主链
2. `report_id` 前缀用 `STREAM-` 与 `execute_hourly` 的 `RPT-` 区分
3. `content_bytes` 只统计本轮实际分析成功的 JSON 大小

## 冻结白名单（仅 1 文件）
1. `services/data/src/researcher/scheduler.py`

## 明确排除
1. `services/data/src/researcher/daily_stats.py` — 不改实现（`record_report` 接口已支持 `content_bytes` 吗？需验收前确认，否则仅加 `elapsed_s` + `success`）
2. `services/data/run_researcher_server.py`
3. 任何 decision、shared、Mini 上的文件
4. `runtime/**`、`logs/**`、真实 `.env`

## 验收标准
1. Alienware 重启 researcher 后，当天 `daily_stats_YYYY-MM-DD.json` 的 `reports_generated` 每轮 stream cycle 完成后 +1。
2. 失败轮（`errors` 非空）也写入，`success=false`，不丢记录。
3. `startup_count` 不重复计数（由 `record_startup` 在服务启动时调用，本单不改）。
4. Decision /api/v1/research/facts/latest 三类 fact 不受影响（主链行为不变）。

## 与 F1 的串行约束
- F2 和 F1 **都改 scheduler.py**
- 必须**串行**：谁先完成 Lockback，另一方 rebase 再提 PR
- 推荐顺序：F2 先（改动极小，风险低）→ F1 后（改动较多，F2 先合并基线更干净）

## 建议最小验证
- 改完本地语法检查：`python -m py_compile services/data/src/researcher/scheduler.py`
- rsync 同步 Alienware 后重启，等一个完整 stream cycle（约 5 分钟），检查：
  ```bash
  ssh 17621@192.168.31.187 "powershell -NoProfile -Command \"Get-Content D:\\researcher_reports\\$(Get-Date -Format yyyy-MM-dd)\\daily_stats_$(Get-Date -Format yyyy-MM-dd).json\""
  ```
- 确认 `reports_generated >= 1`

## 执行责任
- 实施 Agent：`数据`
- 复核：Atlas → 项目架构师终审 → Lockback → rsync 同步 Alienware → docker restart（或直接 supervisord 重启裸 Python 进程）
