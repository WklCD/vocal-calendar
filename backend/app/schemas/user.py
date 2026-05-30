from pydantic import BaseModel
from datetime import datetime


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    avatar_url: str | None
    theme: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    username: str | None = None
    avatar_url: str | None = None
    theme: str | None = None
