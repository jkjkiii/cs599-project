import os
import random

from langchain_core.tools import tool
from utils.config_hander import agent_conf      # 即你 load_agent_config() 返回的 dict
from utils.logger_hander import logger
import requests
from rag.rag_service import RagSummaryService
from utils.path_tool import get_abs_path

# ===================== 高德基础配置 =====================
AMAP_KEY = agent_conf["AMAP_KEY"]
WEATHER_URL = agent_conf.get("AMAP_WEATHER_URL", "https://restapi.amap.com/v3/weather/weatherInfo")
CITY_CODE_URL = agent_conf.get("CITY_CODE_URL", "https://restapi.amap.com/v3/config/district")
rag = RagSummaryService()

user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010",]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
             "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12", ]
external_data = {}
# ===================== 工具函数 =====================
def city2adcode(city_name: str) -> str:
    """将城市名转换为高德 adcode，失败时默认返回北京 110000"""
    try:
        params = {
            "keywords": city_name,
            "key": AMAP_KEY,
            "subdistrict": "0",
            "output": "JSON"
        }
        logger.debug("city2adcode -> URL: %s, params: %s", CITY_CODE_URL, params)
        resp = requests.get(CITY_CODE_URL, params=params, timeout=5)
        logger.debug("city2adcode -> status_code: %s, resp.url: %s", resp.status_code, resp.url)

        try:
            data = resp.json()
        except Exception:
            logger.exception("city2adcode -> JSON解析失败: %s", resp.text)
            return "110000"

        logger.debug("city2adcode -> response json: %s", data)
        if data.get("status") == "1" and data.get("districts"):
            adcode = data["districts"][0].get("adcode")
            logger.debug("city2adcode -> adcode: %s for city: %s", adcode, city_name)
            return adcode

        logger.warning("city2adcode -> 无法解析城市 %s 的 adcode, response: %s", city_name, data)
        return "110000"
    except Exception:
        logger.exception("city2adcode -> 城市代码转换异常: %s", city_name)
        return "110000"

def _resolve_current_city() -> str:
    """使用高德 IP 定位 API 获取当前城市名称（如“北京市”）"""
    try:
        url = "https://restapi.amap.com/v3/ip"
        params = {"key": AMAP_KEY}
        logger.debug("_resolve_current_city -> 请求高德 IP 定位")
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        logger.debug("_resolve_current_city -> 高德 IP 定位返回: %s", data)

        if data.get("status") == "1" and data.get("city"):
            city = data["city"]          # 例如：“北京市”
            logger.info("_resolve_current_city -> 定位城市: %s", city)
            return city

        logger.warning("_resolve_current_city -> 高德 IP 定位失败，响应: %s", data)
    except Exception:
        logger.exception("_resolve_current_city -> 高德 IP 定位异常")

    # 高德失败时，用原接口兜底，但尝试提取城市级名称
    try:
        url = "http://ip-api.com/json/?lang=zh-CN"
        res = requests.get(url, timeout=5)
        data = res.json()
        city = data.get("city", "")
        region = data.get("regionName", "")   # 省份或直辖市
        # 如果 city 是区，region 是市，直接返回 region
        if city and "区" in city and region.endswith("市"):
            logger.info("_resolve_current_city -> 从 ip-api 取到城市: %s", region)
            return region
        if city:
            logger.info("_resolve_current_city -> 从 ip-api 取到城市: %s", city)
            return city
    except Exception:
        logger.exception("_resolve_current_city -> 备用 IP 定位也失败")

    logger.warning("_resolve_current_city -> 全部定位失败，默认返回北京")
    return "北京"

# ===================== 工具定义 =====================
@tool(description="自动获取用户当前真实所在城市名称")
def get_user_location() -> str:
    """返回根据 IP 定位到的城市名称"""
    city = _resolve_current_city()
    logger.info("get_user_location -> %s", city)
    return city

get_current_city = get_user_location  # 别名

@tool(description="获取指定城市天气，不传城市则自动查询当前真实城市天气")
def get_weather(city: str = None) -> str:
    """
    查询城市天气。
    参数 city: 城市名（如“北京”），不填则自动定位当前城市。
    """
    try:
        if not city:
            city = _resolve_current_city()
            logger.info("get_weather -> 自动定位城市: %s", city)

        adcode = city2adcode(city)
        logger.info("get_weather -> adcode: %s", adcode)

        params = {
            "city": adcode,
            "key": AMAP_KEY,
            "extensions": "all",
            "output": "JSON"
        }
        logger.debug("get_weather -> 请求 %s, params: %s", WEATHER_URL, params)
        resp = requests.get(WEATHER_URL, params=params, timeout=5)
        logger.debug("get_weather -> status: %s", resp.status_code)

        data = resp.json()
        logger.debug("get_weather -> response: %s", data)

        if data.get("status") != "1":
            return f"天气查询失败：{data.get('info', '未知错误')}"

        forecast = data["forecasts"][0]["casts"][0]
        return f"{city}今天{forecast['dayweather']}，气温{forecast['nighttemp']}~{forecast['daytemp']}℃"

    except Exception as e:
        logger.exception("get_weather -> 异常: %s", city)
        return f"天气查询异常：{str(e)}"
    
    
@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag.rag_summary(query)

@tool(description="获取用户的ID，以纯字符串形式返回")
def get_user_id() -> str:
    return random.choice(user_ids) 
    
@tool(description="获取当前月份，以纯字符串形式返回")
def get_current_month() -> str:
    return random.choice(month_arr)

def generate_external_data():
    """
    {
        "user_id": {
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            ...
        },
        ...
    }
    :return:
    """
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")

        with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                arr: list[str] = line.strip().split(",")

                user_id: str = arr[0].replace('"', "")
                feature: str = arr[1].replace('"', "")
                efficiency: str = arr[2].replace('"', "")
                consumables: str = arr[3].replace('"', "")
                comparison: str = arr[4].replace('"', "")
                time: str = arr[5].replace('"', "")

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "特征": feature,
                    "效率": efficiency,
                    "耗材": consumables,
                    "对比": comparison,
                }
                


@tool(description="从外部系统中获取指定用户在指定月份的使用记录，以纯字符串形式返回， 如果未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"[fetch_external_data]未能检索到用户：{user_id}在{month}的使用记录数据")
        return ""
    
    

@tool(description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"



# ===================== 测试入口 =====================
if __name__ == "__main__":
    # 测试函数（直接调用）
    print("当前城市:", get_user_location.invoke({}))
    print("当前天气:", get_weather.invoke({"city": None}))
    print("上海天气:", get_weather.invoke({"city": "上海"}))
    power = fetch_external_data.invoke({"user_id": "1001", "month": "2025-01"})
    print("外部数据查询结果:", power)