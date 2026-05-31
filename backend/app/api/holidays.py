from fastapi import APIRouter, Query
from datetime import date
from app.services.holiday_service import HolidayService

router = APIRouter(prefix="/api/holidays", tags=["holidays"])


@router.get("")
async def get_holidays(year: int = Query(...), month: int = Query(...)):
    service = HolidayService()
    holidays = await service.get_holidays(year, month)
    return {"code": 0, "data": holidays, "message": "ok"}


@router.get("/check")
async def check_holiday(date: date = Query(...)):
    service = HolidayService()
    result = await service.is_holiday(date)
    return {"code": 0, "data": result, "message": "ok"}
