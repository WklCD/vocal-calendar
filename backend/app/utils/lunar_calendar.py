from datetime import datetime, date
from typing import Dict, Optional, List
from lunarcalendar import Lunar, Solar, Converter


TRADITIONAL_FESTIVALS = {
    "01-01": "春节",
    "01-15": "元宵节",
    "02-02": "龙抬头",
    "05-05": "端午节",
    "07-07": "七夕节",
    "07-15": "中元节",
    "08-15": "中秋节",
    "09-09": "重阳节",
    "12-08": "腊八节",
    "12-23": "小年",
}


SOLAR_TERMS = {
    "02-03": "立春",
    "02-18": "雨水",
    "03-05": "惊蛰",
    "03-20": "春分",
    "04-04": "清明",
    "04-20": "谷雨",
    "05-05": "立夏",
    "05-21": "小满",
    "06-05": "芒种",
    "06-21": "夏至",
    "07-07": "小暑",
    "07-22": "大暑",
    "08-07": "立秋",
    "08-23": "处暑",
    "09-07": "白露",
    "09-23": "秋分",
    "10-08": "寒露",
    "10-23": "霜降",
    "11-07": "立冬",
    "11-22": "小雪",
    "12-06": "大雪",
    "12-21": "冬至",
}


def solar_to_lunar(year: int, month: int, day: int) -> Dict:
    try:
        solar = Solar(year, month, day)
        lunar = Converter.Solar2Lunar(solar)

        lunar_month = f"{lunar.month:02d}"
        lunar_day = f"{lunar.day:02d}"
        lunar_date_str = f"{lunar_month}-{lunar_day}"

        lunar_info = {
            "lunar_year": lunar.year,
            "lunar_month": lunar.month,
            "lunar_day": lunar.day,
            "lunar_str": f"{lunar.year}年{_get_lunar_month_str(lunar.month)}{_get_lunar_day_str(lunar.day)}",
            "is_leap": lunar.isleap,
            "festival": TRADITIONAL_FESTIVALS.get(lunar_date_str, None),
            "term": None,
        }

        term_key = f"{month:02d}-{day:02d}"
        if term_key in SOLAR_TERMS:
            lunar_info["term"] = SOLAR_TERMS[term_key]

        return lunar_info
    except Exception as e:
        return {
            "error": str(e),
            "lunar_year": year,
            "lunar_month": month,
            "lunar_day": day,
            "lunar_str": f"{year}年{month}月{day}日",
            "is_leap": False,
            "festival": None,
            "term": None,
        }


def lunar_to_solar(year: int, month: int, day: int, leap: bool = False) -> Optional[Dict]:
    try:
        lunar = Lunar(year, month, day, leap)
        solar = Converter.Lunar2Solar(lunar)

        return {
            "solar_year": solar.year,
            "solar_month": solar.month,
            "solar_day": solar.day,
            "solar_str": f"{solar.year}年{solar.month}月{solar.day}日",
            "weekday": solar.weekday,
        }
    except Exception as e:
        return None


def get_month_lunar_calendar(year: int, month: int) -> List[Dict]:
    from calendar import monthrange

    _, days_in_month = monthrange(year, month)
    calendar_data = []

    for day in range(1, days_in_month + 1):
        day_info = solar_to_lunar(year, month, day)
        day_info["solar_date"] = f"{year}-{month:02d}-{day:02d}"
        calendar_data.append(day_info)

    return calendar_data


def get_year_lunar_calendar(year: int) -> Dict[int, List[Dict]]:
    from calendar import monthrange

    year_calendar = {}

    for month in range(1, 13):
        _, days_in_month = monthrange(year, month)
        month_calendar = []

        for day in range(1, days_in_month + 1):
            day_info = solar_to_lunar(year, month, day)
            day_info["solar_date"] = f"{year}-{month:02d}-{day:02d}"
            month_calendar.append(day_info)

        year_calendar[month] = month_calendar

    return year_calendar


def _get_lunar_month_str(month: int) -> str:
    month_str = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
    return f"{month_str[month - 1]}月"


def _get_lunar_day_str(day: int) -> str:
    if day <= 10:
        return f"初{_get_day_str(day)}"
    elif day < 20:
        return f"十{_get_day_str(day - 10)}"
    elif day == 20:
        return "二十"
    elif day < 30:
        return f"廿{_get_day_str(day - 20)}"
    else:
        return "三十"


def _get_day_str(day: int) -> str:
    day_str = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    return day_str[day - 1] if 1 <= day <= 10 else ""


def get_festivals_in_month(year: int, month: int) -> List[Dict]:
    festivals = []
    lunar_cal = get_month_lunar_calendar(year, month)

    for day_info in lunar_cal:
        if day_info.get("festival"):
            festivals.append({
                "date": day_info["solar_date"],
                "name": day_info["festival"],
                "type": "traditional",
                "lunar": f"{day_info['lunar_month']}月{day_info['lunar_day']}日",
            })

        if day_info.get("term"):
            festivals.append({
                "date": day_info["solar_date"],
                "name": day_info["term"],
                "type": "solar_term",
                "lunar": f"{day_info['lunar_str']}",
            })

    return festivals
