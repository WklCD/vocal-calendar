import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    remind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(20), default="push")  # push / voice / both
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / sent / dismissed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    event = relationship("Event", backref="reminders")
