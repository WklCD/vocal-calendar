from pydantic import BaseModel
from datetime import datetime


class CategoryCreateRequest(BaseModel):
    name: str
    color: str = "#4285F4"
    icon: str = "calendar"


class CategoryUpdateRequest(BaseModel):
    name: str | None = None
    color: str | None = None
    icon: str | None = None


class CategoryResponse(BaseModel):
    id: str
    user_id: str
    name: str
    color: str
    icon: str
    created_at: datetime

    class Config:
        from_attributes = True
