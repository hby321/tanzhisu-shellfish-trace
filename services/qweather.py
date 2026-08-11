"""
和风天气API服务模块
数据来源：和风天气 https://dev.qweather.com
提供辽宁沿海实时天气和气象预警数据
"""
import json
import os
import random
import time
import requests
from datetime import datetime, timedelta

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qweather_config.json')

# 缓存：{ location_key: (timestamp, data) }
_cache = {}
CACHE_DURATION = 300  # 5分钟缓存

# 辽宁沿海主要城市坐标（纬度, 经度）
LIAONING_COASTAL_CITIES = {
    '东港': (39.88, 124.15),
    '丹东': (40.00, 124.35),
    '庄河': (39.68, 122.97),
    '盘锦': (40.72, 122.07),
    '营口': (40.67, 122.23),
    '盖州': (40.41, 122.35),
    '锦州': (40.96, 121.13),
    '葫芦岛': (40.71, 120.84),
    '鲅鱼圈': (40.22, 122.12),
    '凤城': (40.45, 123.95),
}


def load_config():
    """加载和风天气配置"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'api_key': '', 'api_host': 'https://devapi.qweather.com'}


def has_api_key():
    """检查是否配置了API Key"""
    config = load_config()
    return bool(config.get('api_key'))


def _get_cache(key):
    """获取缓存"""
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_DURATION:
            return data
    return None


def _set_cache(key, data):
    """设置缓存"""
    _cache[key] = (time.time(), data)


def get_weather_now(lat, lon):
    """
    获取实时天气
    参数：lat 纬度, lon 经度
    返回：dict 或 None
    """
    config = load_config()
    api_key = config.get('api_key', '')
    api_host = config.get('api_host', 'https://devapi.qweather.com')

    if not api_key:
        return None

    # 和风天气location格式：经度,纬度
    location = f"{lon},{lat}"
    cache_key = f"weather_now_{location}"

    # 检查缓存
    cached = _get_cache(cache_key)
    if cached:
        return cached

    url = f"{api_host}/v7/weather/now"
    params = {
        'location': location,
        'key': api_key,
        'lang': 'zh',
        'unit': 'm'
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if data.get('code') == '200' and 'now' in data:
            now = data['now']
            result = {
                'temp': int(now.get('temp', 0)),
                'feels_like': int(now.get('feelsLike', 0)),
                'text': now.get('text', '未知'),
                'icon': now.get('icon', '999'),
                'wind_dir': now.get('windDir', '-'),
                'wind_scale': now.get('windScale', '-'),
                'wind_speed': now.get('windSpeed', '-'),
                'humidity': int(now.get('humidity', 0)),
                'precip': float(now.get('precip', 0)),
                'pressure': int(now.get('pressure', 0)),
                'vis': int(now.get('vis', 0)),
                'cloud': now.get('cloud', '-'),
                'dew': int(now.get('dew', 0)),
                'update_time': data.get('updateTime', ''),
                'source': 'qweather'
            }
            _set_cache(cache_key, result)
            return result
        else:
            print(f"[和风天气] 天气查询失败: code={data.get('code')}, msg={data.get('refer', {}).get('sources', [])}")
            return None
    except Exception as e:
        print(f"[和风天气] 天气请求异常: {e}")
        return None


def get_weather_warning(lat, lon):
    """
    获取实时天气预警（新版API）
    参数：lat 纬度, lon 经度
    返回：list[dict] 或空列表
    """
    config = load_config()
    api_key = config.get('api_key', '')
    api_host = config.get('api_host', 'https://devapi.qweather.com')

    if not api_key:
        return []

    cache_key = f"warning_{lat}_{lon}"

    cached = _get_cache(cache_key)
    if cached:
        return cached

    # 新版API：/weatheralert/v1/current/{lat}/{lon}
    url = f"{api_host}/weatheralert/v1/current/{lat}/{lon}"
    params = {
        'key': api_key,
        'lang': 'zh',
        'localTime': 'true'
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if 'alerts' in data:
            alerts = data.get('alerts', [])
            result = []
            for a in alerts:
                event_type = a.get('eventType', {})
                color_info = a.get('color', {})
                # 转换severity为中文等级
                severity = a.get('severity', '')
                severity_map = {
                    'minor': '蓝色', 'moderate': '黄色',
                    'severe': '橙色', 'extreme': '红色'
                }
                level = severity_map.get(severity, '蓝色')
                result.append({
                    'id': a.get('id', ''),
                    'sender': a.get('senderName', ''),
                    'pub_time': a.get('issuedTime', ''),
                    'title': a.get('headline', ''),
                    'start_time': a.get('effectiveTime', ''),
                    'end_time': a.get('expireTime', ''),
                    'status': 'active',
                    'level': level,
                    'severity': severity,
                    'severity_color': color_info.get('code', ''),
                    'type': event_type.get('code', ''),
                    'type_name': event_type.get('name', ''),
                    'text': a.get('description', a.get('headline', '')),
                    'source': 'qweather'
                })
            _set_cache(cache_key, result)
            return result
        elif data.get('error'):
            print(f"[和风天气] 预警查询失败: {data.get('error', {}).get('title', '')}")
            return []
        else:
            metadata = data.get('metadata', {})
            if metadata.get('zeroResult'):
                _set_cache(cache_key, [])
                return []
            print(f"[和风天气] 预警响应异常: {json.dumps(data, ensure_ascii=False)[:200]}")
            return []
    except Exception as e:
        print(f"[和风天气] 预警请求异常: {e}")
        return []


def get_weather_daily(lat, lon, days=3):
    """
    获取每日天气预报
    参数：lat 纬度, lon 经度, days 天数(3/7/10/15)
    返回：list[dict] 或空列表
    """
    config = load_config()
    api_key = config.get('api_key', '')
    api_host = config.get('api_host', 'https://devapi.qweather.com')

    if not api_key:
        return []

    if days not in (3, 7, 10, 15):
        days = 3

    location = f"{lon},{lat}"
    cache_key = f"daily_{location}_{days}"

    cached = _get_cache(cache_key)
    if cached:
        return cached

    url = f"{api_host}/v7/weather/{days}d"
    params = {
        'location': location,
        'key': api_key,
        'lang': 'zh',
        'unit': 'm'
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if data.get('code') == '200' and 'daily' in data:
            result = []
            for d in data['daily']:
                result.append({
                    'date': d.get('fxDate', ''),
                    'temp_max': int(d.get('tempMax', 0)),
                    'temp_min': int(d.get('tempMin', 0)),
                    'text_day': d.get('textDay', ''),
                    'text_night': d.get('textNight', ''),
                    'icon_day': d.get('iconDay', '999'),
                    'icon_night': d.get('iconNight', '999'),
                    'wind_dir_day': d.get('windDirDay', '-'),
                    'wind_scale_day': d.get('windScaleDay', '-'),
                    'humidity': int(d.get('humidity', 0)),
                    'precip': float(d.get('precip', 0)),
                    'uv_index': d.get('uvIndex', '-'),
                    'source': 'qweather'
                })
            _set_cache(cache_key, result)
            return result
        else:
            print(f"[和风天气] 预报查询失败: code={data.get('code')}")
            return []
    except Exception as e:
        print(f"[和风天气] 预报请求异常: {e}")
        return []


def get_all_coastal_weather():
    """
    获取辽宁所有沿海城市的实时天气
    返回：list[dict]
    """
    results = []
    for city, (lat, lon) in LIAONING_COASTAL_CITIES.items():
        weather = get_weather_now(lat, lon)
        warnings = get_weather_warning(lat, lon)
        results.append({
            'city': city,
            'lat': lat,
            'lon': lon,
            'weather': weather,
            'warnings': warnings,
            'warning_count': len(warnings)
        })
    return results


def get_all_coastal_warnings():
    """
    获取辽宁所有沿海城市的实时天气预警（去重）
    返回：list[dict]
    """
    all_warnings = []
    seen_ids = set()

    for city, (lat, lon) in LIAONING_COASTAL_CITIES.items():
        warnings = get_weather_warning(lat, lon)
        for w in warnings:
            if w['id'] not in seen_ids:
                w['city'] = city
                all_warnings.append(w)
                seen_ids.add(w['id'])

    # 按严重程度排序：红 > 橙 > 黄 > 蓝
    level_order = {'红色': 0, '橙色': 1, '黄色': 2, '蓝色': 3}
    all_warnings.sort(key=lambda w: level_order.get(w.get('level', ''), 4))

    return all_warnings


def get_historical_weather(lat, lon, date_str):
    """
    获取历史天气数据（时光机API，最近10天）
    参数：lat 纬度, lon 经度, date_str 日期字符串(YYYYMMDD)
    返回：dict 或 None
    """
    config = load_config()
    api_key = config.get('api_key', '')
    api_host = config.get('api_host', 'https://devapi.qweather.com')

    if not api_key:
        return None

    cache_key = f"historical_{lat}_{lon}_{date_str}"

    cached = _get_cache(cache_key)
    if cached:
        return cached

    url = f"{api_host}/v7/historical/weather"
    params = {
        'location': f"{lon},{lat}",
        'date': date_str,
        'key': api_key,
        'lang': 'zh'
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if data.get('code') == '200' and 'weatherDaily' in data:
            daily = data['weatherDaily']
            hourly = data.get('weatherHourly', [])
            result = {
                'date': date_str,
                'temp_max': float(daily.get('tempMax', 0)),
                'temp_min': float(daily.get('tempMin', 0)),
                'precip': float(daily.get('precip', 0)),
                'pressure': float(daily.get('pressure', 0)),
                'humidity': float(daily.get('humidity', 0)),
                'sunrise': daily.get('sunrise', ''),
                'sunset': daily.get('sunset', ''),
                'hourly': [
                    {
                        'time': h.get('time', ''),
                        'temp': float(h.get('temp', 0)),
                        'humidity': float(h.get('humidity', 0)),
                        'precip': float(h.get('precip', 0)),
                        'pressure': float(h.get('pressure', 0)),
                        'wind_speed': float(h.get('windSpeed', 0)),
                        'text': h.get('text', '')
                    }
                    for h in hourly
                ],
                'source': 'qweather'
            }
            _set_cache(cache_key, result)
            return result
        else:
            print(f"[和风天气] 历史天气查询失败: code={data.get('code')}, date={date_str}")
            return None
    except Exception as e:
        print(f"[和风天气] 历史天气请求异常: {e}")
        return None


def weather_to_water_quality(weather, flat_id=1):
    """
    将真实气象数据映射为水质参数
    基于海洋学模型：
    - 水温 = f(气温, 水深, 季节) - 水温年振幅约为气温的60%，滞后约2-3个月
    - 盐度 = f(降水量, 蒸发量, 潮汐) - 降水量每增加10mm，盐度降低约0.3‰
    - 溶解氧 = f(水温, 盐度, 生物活性) - 水温每升高1℃，饱和溶氧降低0.25mg/L
    - pH = f(生物光合作用, CO2浓度) - 白天pH升高，夜间降低
    """
    if weather is None:
        return None

    temp_max = weather.get('temp_max', weather.get('temp', 15))
    temp_min = weather.get('temp_min', temp_max - 5)
    precip = weather.get('precip', 0)
    humidity = weather.get('humidity', 60)
    pressure = weather.get('pressure', 1013)

    # 水温映射（基于辽宁沿海实测数据）
    # 辽宁海水温度年振幅约为20-25℃（冬季0℃以下，夏季23-25℃）
    # 气温与水温的关系：水温 ≈ 气温 × 0.5 + 季节偏移
    # 如果只有实时温度，用实时温度估算日均
    if 'temp_max' in weather:
        daily_avg_temp = (temp_max + temp_min) / 2
    else:
        # 实时数据：当前温度 ≈ 日均（误差在±3℃内）
        daily_avg_temp = weather.get('temp', 15)
    
    # 水温 = 日均气温 × 0.55 + 海洋热容量偏移
    # 冬季海水比气温高，夏季比气温低
    month = datetime.now().month
    if month in (12, 1, 2):  # 冬季
        temp_offset = 3
    elif month in (3, 4, 5):  # 春季
        temp_offset = 1
    elif month in (6, 7, 8):  # 夏季
        temp_offset = -2
    else:  # 秋季
        temp_offset = 0

    water_temp = round(max(-2, min(28, daily_avg_temp * 0.55 + temp_offset + random.uniform(-0.5, 0.5))), 1)

    # 盐度映射（基于降水量影响）
    # 辽宁沿海平均盐度：黄海北部30-32‰，辽河口26-30‰
    flat_salinity_bases = {
        1: 31.0,  # 东港1号
        2: 29.0,  # 东港2号（近鸭绿江入海口，低盐）
        3: 31.5,  # 东港3号（水深较深）
        4: 27.5,  # 盘锦1号（辽河口低盐）
        5: 31.0,  # 盘锦2号
        6: 30.0,  # 盖州
    }
    base_salinity = flat_salinity_bases.get(flat_id, 30.0)
    # 降水影响：每10mm降水降低盐度0.3‰
    salinity_reduction = precip * 0.03
    # 蒸发影响：湿度越低蒸发越强，盐度越高
    evaporation_factor = (100 - humidity) * 0.005
    salinity = round(max(15, min(38, base_salinity - salinity_reduction + evaporation_factor + random.uniform(-0.3, 0.3))), 1)

    # 溶解氧映射（基于温度和盐度）
    # 饱和溶解氧公式（简化版）：DO_sat = 14.652 - 0.41022*T + 0.0079910*T² - 0.000037777*T³ - 0.0061988*S + 0.0012227*S*T - 0.000009093*S*T²
    # T: 水温℃, S: 盐度‰
    T = water_temp
    S = salinity
    do_sat = 14.652 - 0.41022*T + 0.0079910*T**2 - 0.000037777*T**3
    do_sat -= 0.0061988*S - 0.0012227*S*T + 0.000009093*S*T**2
    # 实际溶解氧约为饱和值的85-95%（取决于生物活性和水流）
    do_factor = 0.88 + random.uniform(-0.03, 0.05)
    dissolved_oxygen = round(max(1.5, min(12, do_sat * do_factor)), 1)

    # pH映射（基于生物活动和碳酸盐平衡）
    # 正常海水pH 7.8-8.3
    # 水温影响：温度升高，CO2溶解度降低，pH升高
    # 降水影响：淡水输入降低pH
    ph_base = 8.0
    temp_ph_factor = (water_temp - 12) * 0.01  # 温度每偏离12℃，pH变化0.01
    precip_ph_factor = -precip * 0.002  # 降水每1mm，pH降低0.002
    ph = round(max(7.0, min(9.0, ph_base + temp_ph_factor + precip_ph_factor + random.uniform(-0.1, 0.1))), 2)

    return {
        'water_temperature': water_temp,
        'salinity': salinity,
        'dissolved_oxygen': dissolved_oxygen,
        'ph': ph
    }


def get_water_quality_from_weather(lat, lon, flat_id=1):
    """
    基于实时天气推算当前水质
    返回：dict 包含水质参数
    """
    now_weather = get_weather_now(lat, lon)
    if now_weather:
        return weather_to_water_quality(now_weather, flat_id)
    else:
        # 返回基于季节的合理默认值
        month = datetime.now().month
        if month in (12, 1, 2):
            return {'water_temperature': 1.5, 'salinity': 30.5, 'dissolved_oxygen': 9.2, 'ph': 8.1}
        elif month in (3, 4, 5):
            return {'water_temperature': 8.0, 'salinity': 30.0, 'dissolved_oxygen': 7.8, 'ph': 8.0}
        elif month in (6, 7, 8):
            return {'water_temperature': 23.0, 'salinity': 29.5, 'dissolved_oxygen': 5.2, 'ph': 7.9}
        else:
            return {'water_temperature': 12.0, 'salinity': 30.5, 'dissolved_oxygen': 6.5, 'ph': 8.0}


def get_mock_weather():
    """无API Key时返回模拟天气数据"""
    return {
        'temp': 22,
        'feels_like': 21,
        'text': '晴',
        'icon': '100',
        'wind_dir': '东北风',
        'wind_scale': '3',
        'wind_speed': '12',
        'humidity': 58,
        'precip': 0.0,
        'pressure': 1015,
        'vis': 20,
        'cloud': '0',
        'dew': 14,
        'update_time': datetime.now().strftime('%Y-%m-%dT%H:%M'),
        'source': 'mock'
    }


def get_mock_warnings():
    """无API Key时返回模拟预警数据"""
    return []
