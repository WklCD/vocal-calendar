from pydantic import BaseModel
from datetime import datetime


class VoiceCommandRequest(BaseModel):
    text: str


class VoiceCommandResponse(BaseModel):
    intent: str
    entities: dict
    confidence: float
    need_clarify: bool
    clarify_question: str | None = None
    response_text: str


class VoiceLogResponse(BaseModel):
    id: str
    raw_text: str
    parsed_intent: str | None
    parsed_entities: dict | None
    response_text: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class VoiceHelpItem(BaseModel):
    command: str
    example: str
    description: str
