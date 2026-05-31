"""提醒服务 - 管理提醒的创建、查询、处理和关闭。"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.reminder import Reminder
from app.models.event import Event
from app.core.websocket_manager import ws_manager


class ReminderService:
    def __init__(self, db: Session):
        self.db = db

    def create_reminder(
        self, event_id: str, user_id: str, remind_at: datetime, type: str = "push"
    ) -> Reminder:
        """创建单个提醒。"""
        reminder = Reminder(
            event_id=event_id,
            user_id=user_id,
            remind_at=remind_at,
            type=type,
            status="pending",
        )
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def create_reminders_for_event(
        self, event: Event, offsets: list[dict]
    ) -> list[Reminder]:
        """为事件批量创建提醒。

        offsets 格式: [{"offset": -10, "unit": "minutes"}, ...]
        offset 为负数表示提前提醒。
        """
        reminders = []
        for offset_config in offsets:
            offset_value = offset_config["offset"]
            unit = offset_config.get("unit", "minutes")

            kwargs = {unit: offset_value}
            remind_at = event.start_time + timedelta(**kwargs)

            # 不创建已过期的提醒
            if remind_at <= datetime.now(timezone.utc):
                continue

            reminder = self.create_reminder(
                event_id=event.id,
                user_id=event.user_id,
                remind_at=remind_at,
                type=offset_config.get("type", "push"),
            )
            reminders.append(reminder)
        return reminders

    def get_pending_reminders(self) -> list[Reminder]:
        """获取所有待发送且已到时间的提醒。"""
        now = datetime.now(timezone.utc)
        return (
            self.db.query(Reminder)
            .filter(Reminder.status == "pending", Reminder.remind_at <= now)
            .all()
        )

    def get_user_reminders(
        self, user_id: str, status: str | None = None
    ) -> list[Reminder]:
        """获取用户的提醒列表，可按状态过滤。"""
        query = self.db.query(Reminder).filter(Reminder.user_id == user_id)
        if status:
            query = query.filter(Reminder.status == status)
        return query.order_by(Reminder.remind_at.desc()).all()

    def dismiss_reminder(self, reminder_id: str, user_id: str) -> Reminder:
        """关闭一个提醒。"""
        reminder = (
            self.db.query(Reminder)
            .filter(Reminder.id == reminder_id, Reminder.user_id == user_id)
            .first()
        )
        if not reminder:
            raise ValueError("提醒不存在")
        reminder.status = "dismissed"
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    async def process_pending_reminders(self) -> int:
        """处理所有待发送提醒：通过 WebSocket 推送并更新状态。

        返回已处理的提醒数量。
        """
        pending = self.get_pending_reminders()
        processed = 0

        for reminder in pending:
            try:
                event = reminder.event
                message = {
                    "type": "reminder",
                    "data": {
                        "reminder_id": reminder.id,
                        "event_id": reminder.event_id,
                        "event_title": event.title if event else "未知事件",
                        "remind_at": reminder.remind_at.isoformat(),
                        "reminder_type": reminder.type,
                    },
                }
                await ws_manager.send_to_user(reminder.user_id, message)
                reminder.status = "sent"
                processed += 1
            except Exception:
                # 单条提醒失败不影响其他提醒
                continue

        if processed > 0:
            self.db.commit()

        return processed
