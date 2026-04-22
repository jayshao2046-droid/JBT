"""Weather data collector using Open-Meteo API.

采集全球15个关键期货影响地点的天气数据，支持策略决策。
数据源：Open-Meteo Forecast + Archive (ERA5) + NOAA CPC
覆盖：美国农业带、南美、黑海、欧洲、澳洲、东南亚、中国
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

from collectors.base import BaseCollector


class WeatherCollector(BaseCollector):
    """Collect weather data for global commodity-impacting locations via Open-Meteo.

    三源架构：
    - 源1: Open-Meteo Forecast — 16天预报，每日4次更新，免费免Key
    - 源2: Open-Meteo Archive (ERA5) — 历史实况，回溯至1950年，免费免Key
    - 源3: NOAA CPC (ONI + PDO) — ENSO厄尔尼诺/拉尼娜 + 太平洋年代际振荡

    覆盖15个全球关键期货影响地点：
    - 美国农业带：爱荷华(玉米)、堪萨斯(小麦)、圣路易斯(大豆)、孟菲斯(棉花)
    - 美国能源：休斯顿(原油/天然气)、纽约(天然气)
    - 南美洲：巴西马托格罗索(大豆)、圣保罗(咖啡/糖)
    - 黑海/东欧：黑海(小麦)
    - 欧洲：巴黎(小麦)、伦敦(天然气)
    - 澳大利亚：珀斯(小麦)
    - 东南亚：吉隆坡(棕榈油)
    - 中国：郑州(小麦/糖)、哈尔滨(玉米)
    """

    # 15个全球关键期货影响地点
    LOCATIONS = {
        # 美国农业带
        "us_corn_iowa": {"lat": 41.59, "lon": -93.62, "name": "爱荷华(玉米)", "futures": "CBOT.ZC"},
        "us_wheat_kansas": {"lat": 38.84, "lon": -97.61, "name": "堪萨斯(小麦)", "futures": "CBOT.ZW"},
        "us_soy_stlouis": {"lat": 38.63, "lon": -90.20, "name": "圣路易斯(大豆)", "futures": "CBOT.ZS"},
        "us_cotton_memphis": {"lat": 35.15, "lon": -90.05, "name": "孟菲斯(棉花)", "futures": "ICE.CT"},
        # 美国能源
        "us_gulf_houston": {"lat": 29.76, "lon": -95.37, "name": "休斯顿(原油/天然气)", "futures": "NYMEX.CL/NG"},
        "us_natgas_newyork": {"lat": 40.71, "lon": -74.01, "name": "纽约(天然气)", "futures": "NYMEX.NG"},
        # 南美洲
        "br_soy_matogrosso": {"lat": -15.60, "lon": -56.10, "name": "马托格罗索(大豆)", "futures": "CBOT.ZS/ZC"},
        "br_coffee_saopaulo": {"lat": -23.55, "lon": -46.63, "name": "圣保罗(咖啡/糖)", "futures": "ICE.KC/SB"},
        # 黑海/东欧
        "blacksea_wheat": {"lat": 46.48, "lon": 30.73, "name": "黑海(小麦)", "futures": "CBOT.ZW/CZCE.WH"},
        # 欧洲
        "eu_wheat_paris": {"lat": 48.86, "lon": 2.35, "name": "巴黎(小麦)", "futures": "CBOT.ZW"},
        "eu_gas_london": {"lat": 51.51, "lon": -0.13, "name": "伦敦(天然气)", "futures": "NYMEX.NG/ICE.G"},
        # 澳大利亚
        "au_wheat_perth": {"lat": -31.95, "lon": 115.86, "name": "珀斯(小麦)", "futures": "CBOT.ZW"},
        # 东南亚
        "my_palmoil_kl": {"lat": 3.14, "lon": 101.69, "name": "吉隆坡(棕榈油)", "futures": "DCE.p"},
        # 中国
        "cn_wheat_zhengzhou": {"lat": 34.75, "lon": 113.62, "name": "郑州(小麦/糖)", "futures": "CZCE.WH/SR"},
        "cn_corn_harbin": {"lat": 45.75, "lon": 126.65, "name": "哈尔滨(玉米)", "futures": "DCE.c"},
    }

    # 采集字段（仅使用免费版支持的字段）
    WEATHER_VARS = [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "wind_speed_10m_max",
        "weather_code",
    ]

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="weather", **kwargs)
        self.use_mock = use_mock

    def collect(self, *, locations: list[str] | None = None, as_of: str | None = None, days: int = 7) -> list[dict[str, Any]]:
        """采集天气数据。

        Args:
            locations: 地点列表，默认使用全部15个地点
            as_of: 时间戳，默认当前时间
            days: 预报天数，默认7天

        Returns:
            天气数据记录列表
        """
        location_list = locations or list(self.LOCATIONS.keys())
        if self.use_mock:
            raise RuntimeError("mock data is forbidden for weather collector")
        try:
            return self._fetch_live(location_list=location_list, as_of=as_of, days=days)
        except Exception as exc:
            self.logger.error("weather live fetch failed: %s", exc)
            raise

    def _fetch_live(self, *, location_list: list[str], as_of: str | None, days: int) -> list[dict[str, Any]]:
        """从 Open-Meteo 获取实时天气数据。"""
        import httpx
        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()

        for loc_key in location_list:
            loc_info = self.LOCATIONS.get(loc_key)
            if not loc_info:
                self.logger.warning("weather: unknown location %s", loc_key)
                continue

            try:
                # Open-Meteo Forecast API
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": loc_info["lat"],
                    "longitude": loc_info["lon"],
                    "daily": ",".join(self.WEATHER_VARS),
                    "timezone": "auto",
                    "forecast_days": days,
                }

                with httpx.Client(timeout=30.0) as client:
                    resp = client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                time.sleep(0.5)  # 限流

                if "daily" in data:
                    daily = data["daily"]
                    dates = daily.get("time", [])
                    for i, date in enumerate(dates):
                        records.append({
                            "source_type": "weather",
                            "symbol_or_indicator": loc_key,
                            "timestamp": timestamp,
                            "payload": {
                                "location": loc_key,
                                "location_name": loc_info["name"],
                                "futures": loc_info["futures"],
                                "date": date,
                                "temp_max": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                                "temp_min": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                                "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else None,
                                "wind_speed_max": daily.get("wind_speed_10m_max", [])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,
                                "weather_code": daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else None,
                                "mode": "live",
                            },
                        })
                    self.logger.info("weather fetched: location=%s days=%d", loc_key, len(dates))
            except Exception as exc:
                self.logger.warning("weather fetch failed for %s: %s", loc_key, exc)
                continue

        if not records:
            self.logger.warning("weather: no data fetched, returning empty")
        return records

    def _mock_records(self, *, location_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        """生成模拟天气数据（用于测试）。"""
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        records = []
        for loc_key in location_list[:5]:  # 只生成前5个地点的模拟数据
            loc_info = self.LOCATIONS.get(loc_key, {})
            for i in range(3):  # 3天预报
                date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                records.append({
                    "source_type": "weather",
                    "symbol_or_indicator": loc_key,
                    "timestamp": timestamp,
                    "payload": {
                        "location": loc_key,
                        "location_name": loc_info.get("name", loc_key),
                        "futures": loc_info.get("futures", ""),
                        "date": date,
                        "temp_max": 25.0 + i,
                        "temp_min": 15.0 + i,
                        "precipitation": 0.0,
                        "precip_prob": 20,
                        "soil_moisture": 0.3,
                        "evapotranspiration": 3.5,
                        "weather_code": 0,
                        "mode": "mock",
                    },
                })
        self.logger.info("weather mock: generated %d records", len(records))
        return records
