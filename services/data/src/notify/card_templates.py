"""JBT 数据端飞书卡片模板集中管理。

所有卡片严格遵循 JBT 统一通知颜色与卡片标准。
每个函数返回飞书 interactive card 的 payload dict。

卡片类型：
1. collector_start_card   — 采集启动通知
2. collector_done_card    — 采集完成通知（含新鲜度）
3. collector_batch_card   — 定时批量采集汇总
4. collector_fail_card    — 采集失败报警
5. collector_recovery_card— 采集恢复通知
6. alert_card             — P0/P1/P2 通用报警卡（含升级提示）
7. alert_p0_with_buttons  — P0 报警 + 操作按钮
8. news_batch_card        — 30min 新闻批次推送
9. news_breaking_card     — 黑天鹅即时推送
10. device_health_card    — 2h 设备健康报告
11. daily_summary_card    — 收盘飞书精简日报
12. service_lifecycle_card— 服务启停通知
13. recovery_card         — 告警恢复通知
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

CN_TZ = timezone(timedelta(hours=8))
SERVICE_NAME = "BotQuant 资讯 | JBT data-service"

# ── 统一颜色映射 ──────────────────────────────────────────
_TEMPLATE_MAP: dict[str, tuple[str, str]] = {
    "P0": ("red", "🚨"),
    "P1": ("orange", "⚠️"),
    "P2": ("yellow", "🔔"),
    "TRADE": ("grey", "📊"),
    "INFO": ("blue", "📈"),
    "NEWS": ("wathet", "📰"),
    "NOTIFY": ("turquoise", "📣"),
}


def _header(title: str, template: str) -> dict[str, Any]:
    return {
        "title": {"tag": "plain_text", "content": title},
        "template": template,
    }


def _note(extra: str = "") -> dict[str, Any]:
    ts = datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    text = f"{SERVICE_NAME} | {ts}"
    if extra:
        text += f" | {extra}"
    return {
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": text}],
    }


def _hr() -> dict[str, Any]:
    return {"tag": "hr"}


def _md(content: str) -> dict[str, Any]:
    return {"tag": "div", "text": {"tag": "lark_md", "content": content}}


# ═══════════════════════════════════════════════════════════
# 1. 采集启动通知
# ═══════════════════════════════════════════════════════════
def collector_start_card(*, collector_name: str, scheduled: bool = True) -> dict[str, Any]:
    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"📣 [DATA-NOTIFY] {collector_name} 启动", "turquoise"),
            "elements": [
                _md(f"**采集器:** {collector_name}\n**模式:** {'定时调度' if scheduled else '手动触发'}"),
                _hr(),
                _note(),
            ],
        },
    }


# ═══════════════════════════════════════════════════════════
# 2. 采集完成通知（含新鲜度）
# ═══════════════════════════════════════════════════════════
def collector_done_card(
    *,
    collector_name: str,
    record_count: int,
    elapsed_sec: float,
    freshness: str = "",
) -> dict[str, Any]:
    body = (
        f"**采集器:** {collector_name}\n"
        f"**数据条数:** {record_count:,} 条\n"
        f"**耗时:** {elapsed_sec:.1f} 秒"
    )
    if freshness:
        body += f"\n**新鲜度:** {freshness}"
    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"📊 [DATA-TRADE] {collector_name} 完成", "grey"),
            "elements": [_md(body), _hr(), _note()],
        },
    }


# ═══════════════════════════════════════════════════════════
# 3. 定时批量采集汇总
# ═══════════════════════════════════════════════════════════
def collector_batch_card(
    *,
    results: list[dict[str, Any]],
    total_records: int,
    total_elapsed: float,
) -> dict[str, Any]:
    """results: [{"name": str, "records": int, "elapsed": float, "ok": bool}]"""
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count
    icon = "✅" if fail_count == 0 else "⚠️"

    lines = []
    for r in results:
        status = "🟢" if r["ok"] else "🔴"
        lines.append(f"{status} **{r['name']}** {r['records']:,}条 {r['elapsed']:.1f}s")
    body = "\n".join(lines)

    summary = f"**汇总:** {ok_count}/{len(results)} 成功 | {total_records:,} 条 | {total_elapsed:.1f}s"

    template = "grey" if fail_count == 0 else "orange"
    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"{icon} [DATA-TRADE] 批量采集完成 {ok_count}/{len(results)}", template),
            "elements": [_md(body), _hr(), _md(summary), _hr(), _note()],
        },
    }


# ═══════════════════════════════════════════════════════════
# 4. 采集失败报警
# ═══════════════════════════════════════════════════════════
def collector_fail_card(
    *,
    collector_name: str,
    error_msg: str,
    retry_count: int = 0,
    level: str = "P1",
) -> dict[str, Any]:
    template, icon = _TEMPLATE_MAP.get(level, ("orange", "⚠️"))
    body = (
        f"**采集器:** {collector_name}\n"
        f"**错误:** {error_msg[:300]}\n"
        f"**重试次数:** {retry_count}"
    )
    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"{icon} [DATA-{level}] {collector_name} 采集失败", template),
            "elements": [_md(body), _hr(), _note()],
        },
    }


# ═══════════════════════════════════════════════════════════
# 5. 采集恢复通知
# ═══════════════════════════════════════════════════════════
def collector_recovery_card(
    *,
    recovered: list[str],
    still_failed: list[str] | None = None,
) -> dict[str, Any]:
    rec_lines = "\n".join(f"✅ **{s}** 已恢复" for s in recovered)
    elements: list[dict[str, Any]] = [_md(rec_lines)]
    if still_failed:
        fail_lines = "\n".join(f"🔴 **{s}** 仍异常" for s in still_failed)
        elements.extend([_hr(), _md(f"**仍有问题:**\n{fail_lines}")])
    elements.extend([_hr(), _note()])

    color = "green" if not still_failed else "orange"
    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"✅ [DATA-NOTIFY] 采集恢复 — {len(recovered)} 个源已恢复", color),
            "elements": elements,
        },
    }


# ═══════════════════════════════════════════════════════════
# 6. P0/P1/P2 通用报警卡
# ═══════════════════════════════════════════════════════════
def alert_card(
    *,
    level: str,
    title: str,
    body_md: str,
    trace_md: str = "",
    escalated_from: str = "",
) -> dict[str, Any]:
    template, icon = _TEMPLATE_MAP.get(level, ("yellow", "🔔"))
    elements: list[dict[str, Any]] = [_md(body_md)]
    if escalated_from:
        elements.append(_md(f"⬆️ **升级路径:** {escalated_from} → {level}"))
    if trace_md:
        elements.extend([_hr(), _md(trace_md)])
    elements.extend([_hr(), _note()])
    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"JBQ {title}", template),
            "elements": elements,
        },
    }


# ═══════════════════════════════════════════════════════════
# 7. P0 报警 + 操作按钮
# ═══════════════════════════════════════════════════════════
def alert_p0_with_buttons(
    *,
    title: str,
    body_md: str,
    source_name: str = "",
    ops_base_url: str = "",
    ops_token: str = "",
) -> dict[str, Any]:
    elements: list[dict[str, Any]] = [_md(body_md), _hr()]

    if ops_base_url:
        actions: list[dict[str, Any]] = []
        if source_name:
            # 移除 URL 中的 token 参数（安全修复：P1-4）
            # TODO: 后续改为 POST 请求，token 放在请求头中
            actions.append({
                "tag": "button",
                "text": {"tag": "plain_text", "content": "🔄 重启采集器"},
                "url": f"{ops_base_url}/api/v1/ops/restart-collector?source={source_name}",
                "type": "danger",
            })
        actions.append({
            "tag": "button",
            "text": {"tag": "plain_text", "content": "🔧 自动修复"},
            "url": f"{ops_base_url}/api/v1/ops/auto-remediate",
            "type": "primary",
        })
        actions.append({
            "tag": "button",
            "text": {"tag": "plain_text", "content": "📡 查看状态"},
            "url": f"{ops_base_url}/api/v1/health",
            "type": "default",
        })
        elements.append({"tag": "action", "actions": actions})
        elements.append(_hr())

    elements.append(_md("⚠️ **持续超60分钟未恢复，需立即处理！**"))
    elements.extend([_hr(), _note()])

    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"🚨 [DATA-P0] {title}", "red"),
            "elements": elements,
        },
    }


# ═══════════════════════════════════════════════════════════
# 8. 30min 新闻批次推送
# ═══════════════════════════════════════════════════════════
def news_batch_card(
    *,
    category: str,
    items: list[dict[str, Any]],
    total_collected: int = 0,
    total_cleaned: int = 0,
    total_pushed: int = 0,
    dedup_cache_size: int = 0,
) -> dict[str, Any]:
    """items: [{"title": str, "url": str, "source": str, "source_cn": str}]"""
    now_str = datetime.now(CN_TZ).strftime("%H:%M")
    elements: list[dict[str, Any]] = []

    for item in items[:50]:
        source_cn = item.get("source_cn", item.get("source", ""))
        source_tag = f" ({source_cn})" if source_cn else ""
        url = item.get("url", "")
        title_text = (item.get("title", "") or "")[:240]
        if url:
            elements.append(_md(f"• [{title_text}]({url}){source_tag}"))
        else:
            elements.append(_md(f"• {title_text}{source_tag}"))

    elements.append(_hr())
    stats = f"采集总量: {total_collected} | 清洗后: {total_cleaned} | 推送: {total_pushed} | 去重缓存: {dedup_cache_size:,}"
    elements.append(_md(stats))
    elements.append(_note())

    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"📰 [DATA-NEWS] {category}  {now_str}", "wathet"),
            "elements": elements,
        },
    }


# ═══════════════════════════════════════════════════════════
# 9. 黑天鹅即时推送
# ═══════════════════════════════════════════════════════════
def news_breaking_card(
    *,
    title: str,
    url: str = "",
    source_cn: str = "",
    keyword_hit: str = "",
    summary: str = "",
) -> dict[str, Any]:
    body_parts = []
    if url:
        body_parts.append(f"[{title}]({url})")
    else:
        body_parts.append(f"**{title}**")
    if source_cn:
        body_parts.append(f"**来源:** {source_cn}")
    if keyword_hit:
        body_parts.append(f"**关键词命中:** {keyword_hit}")
    if summary:
        body_parts.append(f"**摘要:** {summary[:500]}")

    return {
        "msg_type": "interactive",
        "card": {
            "header": _header("🚨 [DATA-P0] 突发重大新闻", "red"),
            "elements": [_md("\n".join(body_parts)), _hr(), _note()],
        },
    }


# ═══════════════════════════════════════════════════════════
# 10. 2h 设备健康报告
# ═══════════════════════════════════════════════════════════
def device_health_card(
    *,
    cpu_pct: float,
    mem_pct: float,
    disk_pct: float,
    net_latency_ms: float = -1,
    processes: list[dict[str, Any]] | None = None,
    sources: list[dict[str, Any]] | None = None,
    has_issues: bool = False,
) -> dict[str, Any]:
    """processes: [{"label": str, "ok": bool}]
    sources: [{"label": str, "ok": bool, "age_str": str}]
    """
    def _pct_icon(pct: float) -> str:
        return "🔴" if pct >= 85 else ("🟡" if pct >= 70 else "🟢")

    time_str = datetime.now(CN_TZ).strftime("%H:%M")
    color = "red" if has_issues else "green"
    title_icon = "🔴" if has_issues else "⚙️"

    # 资源行
    res = (
        f"**Mini** &nbsp;&nbsp; {_pct_icon(cpu_pct)} CPU {cpu_pct:.0f}%"
        f"  {_pct_icon(mem_pct)} 内存 {mem_pct:.0f}%"
        f"  {_pct_icon(disk_pct)} 磁盘 {disk_pct:.0f}%"
    )
    if net_latency_ms >= 0:
        net_icon = "🟢" if net_latency_ms < 50 else ("🟡" if net_latency_ms < 200 else "🔴")
        res += f"\n**网络延迟:** {net_icon} {net_latency_ms:.1f}ms"

    elements: list[dict[str, Any]] = [_md(res), _hr()]

    # 进程列表
    procs = processes or []
    if procs:
        proc_ok = sum(1 for p in procs if p["ok"])
        proc_icon = "✅" if proc_ok == len(procs) else "⚠️"
        proc_lines = []
        for p in procs:
            icon = "🟢" if p["ok"] else "🔴"
            proc_lines.append(f"{icon} {p['label']}")
        elements.append(_md(f"**守护进程 {proc_ok}/{len(procs)} {proc_icon}**\n" + "\n".join(proc_lines)))
        elements.append(_hr())

    # 采集源新鲜度
    src_list = sources or []
    if src_list:
        src_ok = sum(1 for s in src_list if s["ok"])
        src_icon = "✅" if src_ok == len(src_list) else "⚠️"
        src_lines = []
        for s in src_list:
            icon = "🟢" if s["ok"] else "🔴"
            age = s.get("age_str", "")
            src_lines.append(f"{icon} **{s['label']}** ({age})")
        elements.append(_md(f"**采集源 {src_ok}/{len(src_list)} {src_icon}**\n" + "\n".join(src_lines)))
        elements.append(_hr())

    next_hour = (datetime.now(CN_TZ).hour + 2) % 24
    elements.append(_note(f"下次推送: {next_hour:02d}:{time_str[3:]}"))

    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"{title_icon} Mini 设备健康报告 | {time_str}", color),
            "elements": elements,
        },
    }


# ═══════════════════════════════════════════════════════════
# 11. 收盘飞书精简日报
# ═══════════════════════════════════════════════════════════
def daily_summary_card(
    *,
    total_rounds: int,
    success_rate: float,
    failed_collectors: list[str],
    total_records: int,
    sources_freshness: list[dict[str, Any]],
    cpu_pct: float,
    mem_pct: float,
    disk_pct: float,
    error_count: int,
    news_collected: int,
    news_pushed: int,
    health_score: int,
) -> dict[str, Any]:
    body = (
        f"**📋 采集统计**\n"
        f"总轮次: {total_rounds} | 成功率: {success_rate:.1f}%\n"
        f"数据总条数: {total_records:,} 条\n"
    )
    if failed_collectors:
        body += f"失败采集器: {', '.join(failed_collectors)}\n"

    body += f"\n**📈 数据新鲜度**\n"
    for s in sources_freshness[:8]:
        icon = "🟢" if s.get("ok") else "🔴"
        body += f"{icon} {s['label']} ({s.get('age_str', '')})\n"

    body += (
        f"\n**🖥 设备健康**\n"
        f"CPU: {cpu_pct:.0f}% | 内存: {mem_pct:.0f}% | 磁盘: {disk_pct:.0f}%\n"
        f"\n**📰 新闻统计**\n"
        f"采集: {news_collected:,} | 推送: {news_pushed:,}\n"
        f"\n**📊 健康评分: {health_score}/100 {'✅' if health_score >= 80 else '⚠️'}**"
    )

    color = "green" if health_score >= 80 else ("orange" if health_score >= 60 else "red")
    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"📊 [DATA-INFO] JBT 数据端日报", color),
            "elements": [_md(body), _hr(), _note()],
        },
    }


# ═══════════════════════════════════════════════════════════
# 12. 服务启停通知
# ═══════════════════════════════════════════════════════════
def service_lifecycle_card(
    *,
    action: str,
    version: str = "",
    startup_sec: float = 0,
) -> dict[str, Any]:
    icon = "🟢" if action == "启动" else "🔴"
    body = f"**动作:** {icon} {action}"
    if version:
        body += f"\n**版本:** {version}"
    if startup_sec > 0:
        body += f"\n**启动耗时:** {startup_sec:.1f}s"

    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"📣 [DATA-NOTIFY] 数据服务{action}", "turquoise"),
            "elements": [_md(body), _hr(), _note()],
        },
    }


# ═══════════════════════════════════════════════════════════
# 13. 告警恢复通知
# ═══════════════════════════════════════════════════════════
def recovery_card(*, title: str, detail: str = "") -> dict[str, Any]:
    body = f"✅ {title}"
    if detail:
        body += f"\n{detail}"
    return {
        "msg_type": "interactive",
        "card": {
            "header": _header(f"✅ [DATA-NOTIFY] {title}", "green"),
            "elements": [_md(body), _hr(), _note()],
        },
    }
