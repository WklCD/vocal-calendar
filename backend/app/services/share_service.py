import uuid
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.event import Event


class ShareService:
    def __init__(self, db: Session):
        self.db = db

    def generate_share_token(self, user_id: str) -> str:
        raw = f"{user_id}-{uuid.uuid4()}-{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get_shared_events(self, user_id: str) -> list[Event]:
        return (
            self.db.query(Event)
            .filter(Event.user_id == user_id)
            .order_by(Event.start_time)
            .all()
        )
