import httpx
from typing import Optional


class WeatherService:
    """和风天气 API 服务（Mock 模式，无需 API Key）。"""

    async def get_weather_now(self, location: str = "101010100", lat: Optional[float] = None, lng: Optional[float] = None) -> dict:
        if lat is not None and lng is not None:
            return self._generate_weather_by_coords(lat, lng)
        
        return {
            "temp": "22",
            "text": "晴",
            "icon": "100",
            "humidity": "45",
            "windDir": "东南风",
            "city": "北京",
        }

    async def get_weather_3d(self, location: str = "101010100", lat: Optional[float] = None, lng: Optional[float] = None) -> list[dict]:
        from datetime import date, timedelta

        today = date.today()
        base_temp = 20
        
        if lat is not None and lng is not None:
            base_temp = self._calculate_temp_by_lat(lat)

        return [
            {
                "date": (today + timedelta(days=i)).isoformat(),
                "tempMax": str(base_temp + 5 + (i % 3)),
                "tempMin": str(base_temp - 5 + ((i + 1) % 3)),
                "textDay": self._get_weather_text(lat, lng, i),
                "iconDay": self._get_weather_icon(lat, lng, i),
            }
            for i in range(3)
        ]

    def _generate_weather_by_coords(self, lat: float, lng: float) -> dict:
        temp = self._calculate_temp_by_lat(lat)
        humidity = self._calculate_humidity_by_lat(lat)
        text, icon = self._get_weather_by_region(lat, lng)
        wind_dir = self._get_wind_direction(lng)
        city = self._get_city_by_coords(lat, lng)

        return {
            "temp": str(temp),
            "text": text,
            "icon": icon,
            "humidity": str(humidity),
            "windDir": wind_dir,
            "city": city,
        }

    def _calculate_temp_by_lat(self, lat: float) -> int:
        base_temp = 25
        lat_factor = (90 - abs(lat)) / 90
        return round(base_temp * lat_factor + 10)

    def _calculate_humidity_by_lat(self, lat: float) -> int:
        if abs(lat) < 30:
            return round(70 + (abs(lat) / 30) * 10)
        elif abs(lat) < 60:
            return round(60 + (60 - abs(lat)) / 30 * 20)
        else:
            return round(50 + (90 - abs(lat)) / 30 * 10)

    def _get_weather_by_region(self, lat: float, lng: float) -> tuple[str, str]:
        if lng > 110 and lng < 125 and lat > 20 and lat < 45:
            season = self._get_season()
            if season == "summer":
                return ("晴", "100") if lat > 35 else ("多云", "101")
            elif season == "winter":
                return ("晴", "100") if lat < 30 else ("小雪", "301")
            else:
                return ("多云", "101")
        elif lng > 73 and lng < 95 and lat > 35 and lat < 55:
            return ("晴", "100")
        elif lng > 125 and lng < 135 and lat > 35 and lat < 45:
            return ("多云", "101")
        elif lat < 20:
            return ("雷阵雨", "302")
        elif lat > 60:
            return ("雪", "305")
        else:
            return ("晴", "100")

    def _get_season(self) -> str:
        from datetime import date
        month = date.today().month
        if month in [6, 7, 8]:
            return "summer"
        elif month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        else:
            return "autumn"

    def _get_wind_direction(self, lng: float) -> str:
        directions = ["西北风", "北风", "东北风", "东风", "东南风", "南风", "西南风", "西风"]
        index = round((lng + 180) / 45) % 8
        return directions[index]

    def _get_weather_text(self, lat: Optional[float], lng: Optional[float], day_offset: int) -> str:
        if lat is None or lng is None:
            return "晴"
        
        base_text = self._get_weather_by_region(lat, lng)[0]
        variations = ["晴", "多云", "晴转多云", "多云转晴"]
        return variations[(day_offset + variations.index(base_text)) % len(variations)]

    def _get_weather_icon(self, lat: Optional[float], lng: Optional[float], day_offset: int) -> str:
        icons = {"晴": "100", "多云": "101", "雷阵雨": "302", "小雪": "301", "雪": "305"}
        text = self._get_weather_text(lat, lng, day_offset)
        return icons.get(text, "100")

    def _get_city_by_coords(self, lat: float, lng: float) -> str:
        if lng > 116 and lng < 117 and lat > 39 and lat < 40:
            return "北京"
        elif lng > 121 and lng < 122 and lat > 31 and lat < 32:
            return "上海"
        elif lng > 113 and lng < 114 and lat > 23 and lat < 24:
            return "广州"
        elif lng > 106 and lng < 107 and lat > 29 and lat < 30:
            return "重庆"
        elif lng > 120 and lng < 121 and lat > 30 and lat < 31:
            return "杭州"
        elif lng > 114 and lng < 115 and lat > 22 and lat < 23:
            return "深圳"
        elif lng > 103 and lng < 104 and lat > 30 and lat < 31:
            return "成都"
        elif lng > 118 and lng < 119 and lat > 32 and lat < 33:
            return "南京"
        elif lng > 126 and lng < 127 and lat > 45 and lat < 46:
            return "哈尔滨"
        elif lng > 125 and lng < 126 and lat > 43 and lat < 44:
            return "长春"
        elif lng > 123 and lng < 124 and lat > 41 and lat < 42:
            return "沈阳"
        elif lng > 117 and lng < 118 and lat > 36 and lat < 37:
            return "济南"
        elif lng > 112 and lng < 113 and lat > 34 and lat < 35:
            return "郑州"
        elif lng > 108 and lng < 109 and lat > 34 and lat < 35:
            return "西安"
        elif lng > 102 and lng < 103 and lat > 25 and lat < 26:
            return "昆明"
        elif lng > 110 and lng < 111 and lat > 20 and lat < 21:
            return "海口"
        elif lng > 115 and lng < 116 and lat > 28 and lat < 29:
            return "南昌"
        elif lng > 119 and lng < 120 and lat > 36 and lat < 37:
            return "青岛"
        elif lng > 120 and lng < 121 and lat > 36 and lat < 37:
            return "烟台"
        else:
            return f"位置 ({round(lat, 2)}, {round(lng, 2)})"
