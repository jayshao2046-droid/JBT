"""HTTP client for fetching watchlist from decision service."""

from __future__ import annotations

import logging
from typing import Any

import httpx

_logger = logging.getLogger(__name__)


class WatchlistClient:
    """Fetch dynamic stock watchlist from decision service API."""

    def __init__(
        self,
        decision_service_url: str = "http://localhost:8104",
        timeout: float = 10.0,
    ) -> None:
        self.decision_service_url = decision_service_url.rstrip("/")
        self.timeout = timeout

    def fetch_watchlist(self) -> list[str]:
        """Call GET /api/v1/strategies/watchlist and return stock codes.

        Returns an empty list on network / timeout / unexpected errors.
        """
        url = f"{self.decision_service_url}/api/v1/strategies/watchlist"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data: Any = resp.json()
                # Expect {"watchlist": ["000001", ...]} or plain list
                if isinstance(data, list):
                    return [str(s) for s in data]
                if isinstance(data, dict):
                    wl = data.get("watchlist") or data.get("data") or []
                    return [str(s) for s in wl]
                _logger.warning("Unexpected watchlist response type: %s", type(data))
                return []
        except httpx.TimeoutException:
            _logger.warning("Watchlist request timed out (%s)", url)
            return []
        except httpx.ConnectError:
            _logger.warning("Cannot connect to decision service (%s)", url)
            return []
        except Exception as exc:
            _logger.warning("Failed to fetch watchlist: %s", exc)
            return []
