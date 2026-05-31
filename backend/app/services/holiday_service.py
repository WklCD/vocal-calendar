import httpx
from datetime import date


class HolidayService:
    """中国法定节假日 API 服务。"""

    def __init__(self):
        self.base_url = "https://timor.tech/api/holiday"

    async def get_holidays(self, year: int, month: int) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/info/{year}/{month}")
                response.raise_for_status()
                data = response.json()
                if data.get("code") == 0:
                    holidays = []
                    for day_str, info in data.get("holiday", {}).items():
                        holidays.append(
                            {
                                "date": f"{year}-{month:02d}-{day_str}",
                                "name": info.get("name", ""),
                                "is_holiday": info.get("holiday", False),
                            }
                        )
                    return holidays
        except Exception as e:
            print(f"Holiday API error: {e}")
        return []

    async def is_holiday(self, target_date: date) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/info/{target_date}")
                response.raise_for_status()
                data = response.json()
                if data.get("code") == 0:
                    info = data.get("type", {})
                    return {
                        "is_holiday": info.get("type") == 1,
                        "is_workday": info.get("type") == 2,
                        "name": info.get("name", ""),
                    }
        except Exception as e:
            print(f"Holiday API error: {e}")
        return {"is_holiday": False, "is_workday": False, "name": ""}
