from pydantic import BaseModel
from datetime import datetime


class EventCreateRequest(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    location: str | None = None
    category_id: str | None = None
    priority: int = 3
    color: str | None = None
    recurrence_rule: str | None = None


class EventUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_all_day: bool | None = None
    location: str | None = None
    category_id: str | None = None
    priority: int | None = None
    color: str | None = None
    recurrence_rule: str | None = None


class EventResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str | None
    start_time: datetime
    end_time: datetime
    is_all_day: bool
    location: str | None
    category_id: str | None
    priority: int
    color: str | None
    recurrence_rule: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventSearchParams(BaseModel):
    q: str
    start: datetime | None = None
    end: datetime | None = None
