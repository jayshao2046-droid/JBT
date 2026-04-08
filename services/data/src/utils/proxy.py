"""VPN proxy utilities for overseas data collection.

Migrated from legacy J_BotQuant/src/utils/proxy.py with adaptations:
- Config path uses services/data/configs/vpn.yaml
- Only overseas collectors should call these helpers
- Domestic collectors must NOT use proxy (direct connection)
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import httpx
import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "vpn.yaml"


def _cfg() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def get_proxy_url() -> str:
    """Return the local HTTP proxy URL (e.g. http://127.0.0.1:7890)."""
    port = _cfg().get("proxy_port", 7890)
    return f"http://127.0.0.1:{port}"


def get_proxy_latency_ms() -> float | None:
    """Probe the VPN proxy and return round-trip latency in ms.
    Returns None if proxy is unreachable or too slow.
    """
    cfg = _cfg()
    test_url = cfg.get("test_url", "http://www.gstatic.com/generate_204")
    timeout = cfg.get("health_timeout_sec", 5)
    threshold_ms = cfg.get("alert_threshold_ms", 3000)
    proxy_url = get_proxy_url()
    try:
        t0 = time.monotonic()
        with httpx.Client(proxy=proxy_url, timeout=timeout) as client:
            r = client.get(test_url)
            latency_ms = (time.monotonic() - t0) * 1000
            if r.status_code in (200, 204) and latency_ms < threshold_ms:
                return latency_ms
    except Exception as exc:
        log.debug("VPN proxy probe failed: %s", exc)
    return None


def is_proxy_alive() -> bool:
    """True only when proxy is up and latency is within threshold."""
    return get_proxy_latency_ms() is not None


@contextmanager
def overseas_proxy_env() -> Generator[str | None, None, None]:
    """Temporarily set HTTP_PROXY env vars for overseas collectors."""
    proxy_url = get_proxy_url() if is_proxy_alive() else None
    if not proxy_url:
        log.warning("VPN proxy not available; overseas requests will be skipped or may fail")
        yield None
        return

    env_keys = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")
    saved = {k: os.environ.get(k) for k in env_keys}
    for k in env_keys:
        os.environ[k] = proxy_url
    try:
        latency = get_proxy_latency_ms()
        log.info("VPN proxy active: %s  latency=%.0f ms", proxy_url, latency or 0)
        yield proxy_url
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def get_overseas_httpx_client(**kwargs) -> httpx.AsyncClient:
    """Return an httpx.AsyncClient routed through the VPN proxy."""
    if not is_proxy_alive():
        raise RuntimeError("VPN proxy is not available; cannot create overseas httpx client")
    return httpx.AsyncClient(proxy=get_proxy_url(), **kwargs)


def get_httpx_proxy_kwargs() -> dict:
    """返回 httpx 客户端代理参数，不可用时返回空 dict（直连）。"""
    if is_proxy_alive():
        return {"proxy": get_proxy_url()}
    log.warning("代理不可用，httpx 将直连")
    return {}


# 境外连通测试目标（覆盖所有需要代理的域名类别）
OVERSEAS_TARGETS: dict[str, str] = {
    "google_204":    "http://www.gstatic.com/generate_204",
    "yahoo_finance": "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=1d&interval=1d",
    "reuters":       "https://www.reuters.com/",
    "investing":     "https://www.investing.com/",
    "noaa":          "https://www.cpc.ncep.noaa.gov/",
}


def check_overseas_targets() -> dict[str, float | None]:
    """测试全部境外目标的连通性，返回 {target_name: latency_ms | None}。"""
    results: dict[str, float | None] = {}
    cfg = _cfg()
    threshold_ms = cfg.get("alert_threshold_ms", 5000)
    timeout = cfg.get("health_timeout_sec", 8)
    proxy_url = get_proxy_url()
    for name, url in OVERSEAS_TARGETS.items():
        try:
            t0 = time.monotonic()
            with httpx.Client(proxy=proxy_url, timeout=timeout) as client:
                r = client.get(url)
                latency_ms = (time.monotonic() - t0) * 1000
                if r.status_code in (200, 204, 301, 302, 403) and latency_ms < threshold_ms:
                    results[name] = round(latency_ms, 1)
                else:
                    results[name] = None
        except Exception:
            results[name] = None
    return results


def check_and_report() -> bool:
    """P0 health check. Logs result and returns True if OK."""
    latency = get_proxy_latency_ms()
    if latency is not None:
        log.info("VPN proxy OK — latency=%.0f ms  url=%s", latency, get_proxy_url())
        return True

    log.error("VPN proxy UNREACHABLE — url=%s", get_proxy_url())
    return False
