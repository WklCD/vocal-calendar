from fastapi import APIRouter, Query
from typing import Optional
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/now")
async def get_weather_now(
    location: str = Query("101010100"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None)
):
    service = WeatherService()
    weather = await service.get_weather_now(location, lat, lng)
    return {"code": 0, "data": weather, "message": "ok"}


@router.get("/forecast")
async def get_weather_forecast(
    location: str = Query("101010100"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None)
):
    service = WeatherService()
    forecast = await service.get_weather_3d(location, lat, lng)
    return {"code": 0, "data": forecast, "message": "ok"}
