#!/usr/bin/env python3
"""全量数据清洗与研读 — 一次性扫描 Mini 全部数据，生成完整报告

直接 SSH 到 Mini 读取 parquet 数据，不走 API（API 的 symbol 映射有问题）。
生成结果:
  1. runtime/researcher/reports/inventory.json        — 数据资产盘点
  2. runtime/researcher/reports/futures_daily.json     — 期货日线摘要
  3. runtime/researcher/reports/macro_overview.json    — 宏观数据概览
  4. runtime/researcher/reports/news_digest.json       — 新闻情绪摘要
  5. runtime/researcher/reports/full_analysis.json     — LLM 全量研判
  6. 推送飞书卡片 + 推送报告到 Mini data API
"""

import asyncio
import json
import os
import sys
import subprocess
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# 加载 .env
_env_file = Path(__file__).resolve().parent / ".env.researcher"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("full_scan")

MINI_SSH = "jaybot@192.168.31.156"
MINI_DATA_ROOT = "/Users/jaybot/jbt/data"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://192.168.31.187:11434")
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK_URL", "")
REPORTS_DIR = Path("runtime/researcher/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def ssh_exec(cmd: str, timeout: int = 60) -> str:
    """
    SSH 执行远程 Python 命令

    P0-4 修复：添加命令验证，防止命令注入
    注意：当前仅用于执行硬编码的 Python 脚本，不接受用户输入
    """
    # P0-4 安全检查：命令长度限制
    if not isinstance(cmd, str) or len(cmd) > 10000:
        logger.error(f"Invalid command: length={len(cmd) if isinstance(cmd, str) else 'N/A'}")
        return ""

    # P0-4 安全检查：命令必须以 python3 -c 开头（硬编码脚本模式）
    if not cmd.startswith('python3 -c'):
        logger.error(f"Invalid command format: must start with 'python3 -c'")
        return ""

    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", MINI_SSH, cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"SSH exec failed: {e}")
        return ""


# ── 第 1 步: 数据资产盘点 ──────────────────────────

def scan_inventory() -> dict:
    """扫描 Mini 全量数据资产"""
    logger.info(">>> 第 1 步: 数据资产盘点...")

    script = '''python3 -c "
import pyarrow.parquet as pq, os, json
root = '/Users/jaybot/jbt/data'
result = {'futures_daily':[], 'futures_1min':[], 'stock_minute':[], 'news':[], 'macro':[], 'other':[]}
for d in sorted(os.listdir(root)):
    dp = os.path.join(root, d)
    if not os.path.isdir(dp): continue
    daily = os.path.join(dp, 'daily', 'records.parquet')
    m1 = os.path.join(dp, '1min', 'records.parquet')
    sm = os.path.join(dp, 'stock_minute', 'records.parquet')
    if os.path.exists(daily):
        t = pq.read_table(daily)
        df = t.to_pandas()
        last = str(df['timestamp'].iloc[-1]) if len(df)>0 else 'N/A'
        result['futures_daily'].append({'symbol':d, 'rows':t.num_rows, 'last':last})
    elif os.path.exists(m1):
        result['futures_1min'].append({'symbol':d, 'rows':pq.read_table(m1).num_rows})
    elif os.path.exists(sm):
        result['stock_minute'].append({'symbol':d, 'rows':pq.read_table(sm).num_rows})
    elif d in ('news_api','news_collected','news_rss','news_score','rss_news','sentiment','social','social_score','fear_greed'):
        files = list(os.walk(dp))
        fc = sum(len(f) for _,_,f in files)
        result['news'].append({'name':d, 'files':fc})
    elif d.startswith(('CN_','US_','EU_','JP_','UK_','AU_','CA_','CPI','PMI','bdi','bci','bcti','bpi','bsi')):
        result['macro'].append(d)
    else:
        result['other'].append(d)
print(json.dumps(result, ensure_ascii=False))
"'''
    raw = ssh_exec(script, timeout=120)
    if raw:
        inventory = json.loads(raw)
        (REPORTS_DIR / "inventory.json").write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"  期货日线: {len(inventory['futures_daily'])} 品种")
        logger.info(f"  期货分钟: {len(inventory['futures_1min'])} 品种")
        logger.info(f"  A股分钟: {len(inventory['stock_minute'])} 只")
        logger.info(f"  新闻情绪: {len(inventory['news'])} 源")
        logger.info(f"  宏观数据: {len(inventory['macro'])} 指标")
        return inventory
    return {}


# ── 第 2 步: 期货日线摘要 ──────────────────────────

def scan_futures_daily() -> dict:
    """读取所有期货日线，生成最新行情摘要"""
    logger.info(">>> 第 2 步: 期货日线数据清洗...")

    script = '''python3 -c "
import pyarrow.parquet as pq, os, json
root = '/Users/jaybot/jbt/data'
summaries = []
for d in sorted(os.listdir(root)):
    daily = os.path.join(root, d, 'daily', 'records.parquet')
    if not os.path.exists(daily): continue
    try:
        df = pq.read_table(daily).to_pandas()
        if len(df) < 2: continue
        last = df.iloc[-1]
        prev = df.iloc[-2]
        chg = float(last['close']) - float(prev['close'])
        chg_pct = chg / float(prev['close']) * 100 if float(prev['close']) != 0 else 0
        summaries.append({
            'symbol': d,
            'date': str(last['timestamp']),
            'open': float(last['open']),
            'high': float(last['high']),
            'low': float(last['low']),
            'close': float(last['close']),
            'volume': int(last['volume']) if 'volume' in df.columns else 0,
            'oi': int(last['oi']) if 'oi' in df.columns else 0,
            'change': round(chg, 2),
            'change_pct': round(chg_pct, 2),
            'total_bars': len(df),
        })
    except Exception as e:
        logger.warning(f"Error processing symbol {sym}: {e}")
print(json.dumps(summaries, ensure_ascii=False))
"'''
    raw = ssh_exec(script, timeout=120)
    if raw:
        data = json.loads(raw)
        (REPORTS_DIR / "futures_daily.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"  扫描完成: {len(data)} 个期货品种")

        # 分类: 涨跌排行
        up = sorted([s for s in data if s['change_pct'] > 0], key=lambda x: -x['change_pct'])
        down = sorted([s for s in data if s['change_pct'] < 0], key=lambda x: x['change_pct'])
        flat = [s for s in data if s['change_pct'] == 0]
        return {"all": data, "top_up": up[:10], "top_down": down[:10], "flat": flat}
    return {}


# ── 第 3 步: 新闻情绪摘要 ──────────────────────────

def scan_news() -> dict:
    """读取 Mini 新闻数据，生成最新新闻摘要"""
    logger.info(">>> 第 3 步: 新闻数据清洗...")

    script = '''python3 -c "
import os, json
root = '/Users/jaybot/jbt/data'
results = {}
for news_dir in ('news_collected', 'news_rss', 'news_api', 'rss_news'):
    dp = os.path.join(root, news_dir)
    if not os.path.isdir(dp): continue
    items = []
    for r, ds, fs in os.walk(dp):
        for f in sorted(fs)[-50:]:  # 每个目录最多取最新50条
            fp = os.path.join(r, f)
            try:
                if f.endswith('.json'):
                    with open(fp,'r',encoding='utf-8') as fh:
                        d = json.load(fh)
                        if isinstance(d, list):
                            items.extend(d[-10:])
                        elif isinstance(d, dict):
                            items.append(d)
            except Exception as e:
                logger.warning(f"Error reading news file {fp}: {e}")
    results[news_dir] = {'count': len(items), 'latest': items[-20:] if items else []}
# sentiment
sd = os.path.join(root, 'sentiment')
if os.path.isdir(sd):
    sfiles = []
    for r,ds,fs in os.walk(sd):
        for f in sorted(fs)[-10:]:
            fp = os.path.join(r,f)
            try:
                if f.endswith('.json'):
                    with open(fp,'r',encoding='utf-8') as fh:
                        sfiles.append(json.load(fh))
            except Exception as e:
                logger.warning(f"Error reading sentiment file {fp}: {e}")
    results['sentiment'] = {'count':len(sfiles), 'latest':sfiles[-5:]}
print(json.dumps(results, ensure_ascii=False, default=str))
"'''
    raw = ssh_exec(script, timeout=120)
    if raw:
        data = json.loads(raw)
        (REPORTS_DIR / "news_digest.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for k, v in data.items():
            logger.info(f"  {k}: {v.get('count', 0)} 条")
        return data
    return {}


# ── 第 4 步: 宏观数据概览 ──────────────────────────

def scan_macro() -> dict:
    """读取宏观经济数据"""
    logger.info(">>> 第 4 步: 宏观数据清洗...")

    script = '''python3 -c "
import os, json
root = '/Users/jaybot/jbt/data'
macro_dirs = [d for d in os.listdir(root) if d.startswith(('CN_','US_','EU_','JP_','UK_','AU_','CA_','CPI','PMI'))]
results = {}
for d in sorted(macro_dirs):
    dp = os.path.join(root, d)
    if not os.path.isdir(dp): continue
    files = []
    for r,ds,fs in os.walk(dp):
        for f in sorted(fs)[-5:]:
            fp = os.path.join(r, f)
            try:
                if f.endswith('.json'):
                    with open(fp,'r',encoding='utf-8') as fh:
                        files.append(json.load(fh))
                elif f.endswith('.parquet'):
                    import pyarrow.parquet as pq
                    t = pq.read_table(fp)
                    files.append({'rows': t.num_rows, 'columns': t.column_names})
            except Exception as e:
                logger.warning(f"Error reading macro file {fp}: {e}")
    results[d] = {'files_count': len(files), 'latest': files[-1] if files else None}
print(json.dumps(results, ensure_ascii=False, default=str))
"'''
    raw = ssh_exec(script, timeout=120)
    if raw:
        data = json.loads(raw)
        (REPORTS_DIR / "macro_overview.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"  宏观指标: {len(data)} 个")
        return data
    return {}


# ── 第 5 步: LLM 全量研判 ──────────────────────────

async def llm_full_analysis(futures: dict, news: dict, macro: dict) -> str:
    """用 qwen3:14b 生成全量研判报告"""
    logger.info(">>> 第 5 步: LLM 全量研判...")

    # 构建 prompt
    top_up = futures.get("top_up", [])[:5]
    top_down = futures.get("top_down", [])[:5]

    up_text = "\n".join([f"  {s['symbol']}: {s['close']} ({s['change_pct']:+.2f}%)" for s in top_up])
    down_text = "\n".join([f"  {s['symbol']}: {s['close']} ({s['change_pct']:+.2f}%)" for s in top_down])

    # 新闻摘要
    news_text = ""
    for src, info in news.items():
        if isinstance(info, dict) and info.get("latest"):
            for item in info["latest"][-5:]:
                if isinstance(item, dict):
                    title = item.get("title", item.get("headline", str(item)[:80]))
                    news_text += f"  - {title}\n"

    # 宏观摘要
    macro_text = ", ".join(list(macro.keys())[:15])

    prompt = f"""你是一位资深期货与宏观分析师。请根据以下数据生成一份完整的市场研判报告（中文）。

## 期货涨幅前五
{up_text}

## 期货跌幅前五
{down_text}

## 总计品种数: {len(futures.get('all', []))}

## 最新新闻摘要
{news_text if news_text else '暂无最新新闻'}

## 宏观数据覆盖
{macro_text if macro_text else '暂无宏观数据'}

请输出:
1. 整体市场研判（多头/空头/震荡）
2. 板块分析（黑色、有色、能化、农产品、贵金属、股指）
3. 重点关注品种及操作建议
4. 风险提示
5. 明日关注要点

要求：简洁专业，信息密度高，适合交易员快速阅读。"""

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "qwen3:14b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_ctx": 8192}
                },
                timeout=180.0
            )
            result = resp.json()
            analysis = result.get("response", "")
            duration = result.get("total_duration", 0) / 1e9
            logger.info(f"  LLM 完成，耗时 {duration:.1f}s，字数 {len(analysis)}")
            return analysis
    except Exception as e:
        logger.error(f"  LLM 失败: {e}")
        return f"LLM 分析失败: {e}"


# ── 第 6 步: 推送飞书 ──────────────────────────────

async def push_feishu(analysis: str, futures: dict, inventory: dict):
    """推送全量研读报告到飞书"""
    if not FEISHU_WEBHOOK:
        logger.warning("  飞书 webhook 未配置，跳过推送")
        return

    logger.info(">>> 第 6 步: 推送飞书卡片...")

    now = datetime.now()
    total_futures = len(futures.get("all", []))
    total_stocks = len(inventory.get("stock_minute", []))

    # 截取 LLM 分析前 800 字
    brief = analysis[:800] + ("..." if len(analysis) > 800 else "")

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📈 [JBT 数据研究员-全量扫描] {now.strftime('%Y-%m-%d %H:%M')}"},
                "template": "blue"
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**数据盘点**\n期货: {total_futures} 品种 | A股: {total_stocks} 只\n\n**全量研判**\n{brief}"}},
                {"tag": "hr"},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": f"JBT 数据研究员 | {now.strftime('%H:%M')} | 全量数据清洗 | Alienware"}]}
            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(FEISHU_WEBHOOK, json=card, timeout=10.0)
            logger.info(f"  飞书推送: {resp.status_code}")
    except Exception as e:
        logger.error(f"  飞书推送失败: {e}")


# ── 主入口 ───────────────────────────────────────────

async def main():
    start = time.time()
    logger.info("=" * 60)
    logger.info("JBT 数据研究员 — 全量数据清洗与研读")
    logger.info(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"  Mini: {MINI_SSH}")
    logger.info(f"  Ollama: {OLLAMA_URL}")
    logger.info("=" * 60)

    # 1. 盘点
    inventory = scan_inventory()

    # 2. 期货日线
    futures = scan_futures_daily()

    # 3. 新闻
    news = scan_news()

    # 4. 宏观
    macro = scan_macro()

    # 5. LLM 研判
    analysis = await llm_full_analysis(futures, news, macro)

    # 保存完整分析
    full_report = {
        "generated_at": datetime.now().isoformat(),
        "scan_type": "full",
        "inventory_summary": {
            "futures_daily": len(inventory.get("futures_daily", [])),
            "futures_1min": len(inventory.get("futures_1min", [])),
            "stock_minute": len(inventory.get("stock_minute", [])),
            "news_sources": len(inventory.get("news", [])),
            "macro_indicators": len(inventory.get("macro", [])),
        },
        "futures_top_up": futures.get("top_up", [])[:5],
        "futures_top_down": futures.get("top_down", [])[:5],
        "llm_analysis": analysis,
        "elapsed_seconds": round(time.time() - start, 1),
    }

    (REPORTS_DIR / "full_analysis.json").write_text(
        json.dumps(full_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 6. 推送飞书
    await push_feishu(analysis, futures, inventory)

    elapsed = time.time() - start
    logger.info("=" * 60)
    logger.info(f"全量扫描完成，总耗时 {elapsed:.1f}s")
    logger.info(f"报告目录: {REPORTS_DIR.absolute()}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
