from pydantic import BaseModel
from datetime import datetime


class ReminderCreateRequest(BaseModel):
    event_id: str
    remind_at: datetime
    type: str = "push"


class ReminderResponse(BaseModel):
    id: str
    event_id: str
    user_id: str
    remind_at: datetime
    type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReminderDismissRequest(BaseModel):
    reminder_id: str
