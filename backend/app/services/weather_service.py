import httpx


class WeatherService:
    """和风天气 API 服务（Mock 模式，无需 API Key）。"""

    async def get_weather_now(self, location: str = "101010100") -> dict:
        # 返回模拟天气数据（无需真实 API Key）
        return {
            "temp": "22",
            "text": "晴",
            "icon": "100",
            "humidity": "45",
            "windDir": "东南风",
        }

    async def get_weather_3d(self, location: str = "101010100") -> list[dict]:
        from datetime import date, timedelta

        today = date.today()
        return [
            {
                "date": (today + timedelta(days=i)).isoformat(),
                "tempMax": "25",
                "tempMin": "15",
                "textDay": "晴",
                "iconDay": "100",
            }
            for i in range(3)
        ]
