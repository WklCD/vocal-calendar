from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.event import Event


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def create_event(self, user_id: str, **kwargs) -> Event:
        event = Event(user_id=user_id, **kwargs)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_events(self, user_id: str, start: datetime, end: datetime) -> list[Event]:
        return (
            self.db.query(Event)
            .filter(Event.user_id == user_id, Event.start_time >= start, Event.start_time <= end)
            .order_by(Event.start_time)
            .all()
        )

    def get_event_by_id(self, event_id: str, user_id: str) -> Event | None:
        return self.db.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()

    def update_event(self, event_id: str, user_id: str, **kwargs) -> Event:
        event = self.get_event_by_id(event_id, user_id)
        if not event:
            raise ValueError("事件不存在")
        for key, value in kwargs.items():
            if value is not None and hasattr(event, key):
                setattr(event, key, value)
        self.db.commit()
        self.db.refresh(event)
        return event

    def delete_event(self, event_id: str, user_id: str) -> bool:
        event = self.get_event_by_id(event_id, user_id)
        if not event:
            raise ValueError("事件不存在")
        self.db.delete(event)
        self.db.commit()
        return True

    def search_events(self, user_id: str, query: str) -> list[Event]:
        return (
            self.db.query(Event)
            .filter(
                Event.user_id == user_id,
                or_(Event.title.ilike(f"%{query}%"), Event.description.ilike(f"%{query}%"), Event.location.ilike(f"%{query}%")),
            )
            .order_by(Event.start_time.desc())
            .all()
        )
