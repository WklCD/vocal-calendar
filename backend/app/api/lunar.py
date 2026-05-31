from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.utils.lunar_calendar import (
    solar_to_lunar,
    get_month_lunar_calendar,
    get_year_lunar_calendar,
    get_festivals_in_month
)
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


router = APIRouter(prefix="/api/lunar", tags=["lunar"])


class LunarDateResponse(BaseModel):
    lunar_year: int
    lunar_month: int
    lunar_day: int
    lunar_str: str
    is_leap: bool
    festival: Optional[str] = None
    term: Optional[str] = None


class FestivalResponse(BaseModel):
    date: str
    name: str
    type: str
    lunar: str


@router.get("/convert/{year}/{month}/{day}", response_model=LunarDateResponse)
async def convert_solar_to_lunar(
    year: int,
    month: int,
    day: int
):
    result = solar_to_lunar(year, month, day)
    return result


@router.get("/month/{year}/{month}")
async def get_month_lunar(
    year: int,
    month: int
):
    calendar_data = get_month_lunar_calendar(year, month)
    return {
        "year": year,
        "month": month,
        "calendar": calendar_data,
    }


@router.get("/year/{year}")
async def get_year_lunar(year: int):
    calendar_data = get_year_lunar_calendar(year)
    return {
        "year": year,
        "months": calendar_data,
    }


@router.get("/festivals/{year}/{month}", response_model=List[FestivalResponse])
async def get_month_festivals(year: int, month: int):
    festivals = get_festivals_in_month(year, month)
    return festivals


@router.get("/today")
async def get_today_lunar():
    today = datetime.now()
    lunar_info = solar_to_lunar(today.year, today.month, today.day)
    return {
        "solar_date": today.strftime("%Y-%m-%d"),
        "lunar": lunar_info,
    }
