import os
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WeatherServer")
AMAP_KEY = os.getenv("AMAP_KEY", "")

WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"
CITY_CODE_URL = "https://restapi.amap.com/v3/config/district"


def _resolve_city() -> str:
    """IP 定位获取当前城市，失败兜底为北京"""
    try:
        resp = requests.get(
            "https://restapi.amap.com/v3/ip",
            params={"key": AMAP_KEY},
            timeout=5,
        )
        data = resp.json()
        if data.get("city"):
            return data["city"]
    except Exception:
        pass

    # 备用：ip-api.com
    try:
        resp = requests.get("http://ip-api.com/json/?lang=zh-CN", timeout=5)
        data = resp.json()
        city = data.get("city", "")
        region = data.get("regionName", "")
        if city and "区" in city and region.endswith("市"):
            return region
        if city:
            return city
    except Exception:
        pass

    return "北京"


def _city2adcode(city_name: str) -> str:
    """城市名 → 高德 adcode"""
    try:
        resp = requests.get(
            CITY_CODE_URL,
            params={"keywords": city_name, "key": AMAP_KEY, "subdistrict": "0"},
            timeout=5,
        )
        data = resp.json()
        if data.get("status") == "1" and data.get("districts"):
            return data["districts"][0].get("adcode")
    except Exception:
        pass
    return "110000"


@mcp.tool()
def get_location() -> str:
    """自动获取当前用户所在城市名称，无需任何参数"""
    city = _resolve_city()
    return city


@mcp.tool()
def get_weather(city: str = None) -> str:
    """查询指定城市天气

    参数:
        city: 城市名称（如"北京"），不填则自动定位当前城市
    """
    if not city:
        city = _resolve_city()

    adcode = _city2adcode(city)

    resp = requests.get(
        WEATHER_URL,
        params={"city": adcode, "key": AMAP_KEY, "extensions": "all"},
        timeout=5,
    )
    data = resp.json()

    if data.get("status") != "1":
        return f"天气查询失败：{data.get('info', '未知错误')}"

    forecast = data["forecasts"][0]["casts"][0]
    return f"{city}今天{forecast['dayweather']}，气温{forecast['nighttemp']}~{forecast['daytemp']}℃"


if __name__ == "__main__":
    mcp.run()
