import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.services.reminder_service import ReminderService
from app.models.reminder import Reminder
from app.models.event import Event


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.fixture
def service(db):
    return ReminderService(db)


class TestCreateReminder:
    def test_create_reminder(self, service, db):
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        now = datetime.now(timezone.utc)
        reminder = service.create_reminder(
            event_id="event-1", user_id="user-1", remind_at=now, type="push"
        )
        assert db.add.called
        assert db.commit.called
        assert db.refresh.called

    def test_create_reminder_default_type(self, service, db):
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        now = datetime.now(timezone.utc)
        reminder = service.create_reminder(
            event_id="event-1", user_id="user-1", remind_at=now
        )
        db.add.assert_called_once()


class TestCreateRemindersForEvent:
    def test_create_reminders_for_event(self, service, db):
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        event = Event(
            id="event-1",
            user_id="user-1",
            title="测试事件",
            start_time=future_time,
            end_time=future_time + timedelta(hours=1),
        )
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        offsets = [
            {"offset": -10, "unit": "minutes"},
            {"offset": -30, "unit": "minutes"},
        ]
        reminders = service.create_reminders_for_event(event, offsets)
        assert len(reminders) == 2
        assert db.add.call_count == 2

    def test_create_reminders_skips_past(self, service, db):
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        event = Event(
            id="event-1",
            user_id="user-1",
            title="过去的事件",
            start_time=past_time,
            end_time=past_time + timedelta(hours=1),
        )
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        offsets = [{"offset": -10, "unit": "minutes"}]
        reminders = service.create_reminders_for_event(event, offsets)
        assert len(reminders) == 0
        assert not db.add.called


class TestGetPendingReminders:
    def test_get_pending_reminders(self, service, db):
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        db.query.return_value = mock_query
        reminders = service.get_pending_reminders()
        assert isinstance(reminders, list)


class TestGetUserReminders:
    def test_get_user_reminders_no_filter(self, service, db):
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = mock_query
        reminders = service.get_user_reminders("user-1")
        assert isinstance(reminders, list)

    def test_get_user_reminders_with_status(self, service, db):
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = mock_query
        reminders = service.get_user_reminders("user-1", status="pending")
        assert isinstance(reminders, list)


class TestDismissReminder:
    def test_dismiss_reminder_success(self, service, db):
        mock_reminder = Reminder(
            id="reminder-1", event_id="event-1", user_id="user-1",
            remind_at=datetime.now(timezone.utc), type="push", status="pending"
        )
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_reminder
        db.query.return_value = mock_query
        db.commit = MagicMock()
        db.refresh = MagicMock()

        result = service.dismiss_reminder("reminder-1", "user-1")
        assert mock_reminder.status == "dismissed"
        assert db.commit.called

    def test_dismiss_reminder_not_found(self, service, db):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_query

        with pytest.raises(ValueError, match="提醒不存在"):
            service.dismiss_reminder("nonexistent", "user-1")


class TestProcessPendingReminders:
    @pytest.mark.asyncio
    async def test_process_pending_reminders_sends_and_updates(self, service, db):
        mock_event = Event(
            id="event-1", user_id="user-1", title="会议",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        mock_reminder = Reminder(
            id="reminder-1", event_id="event-1", user_id="user-1",
            remind_at=datetime.now(timezone.utc), type="push", status="pending",
        )
        mock_reminder.event = mock_event

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_reminder]
        db.query.return_value = mock_query
        db.commit = MagicMock()

        with patch("app.services.reminder_service.ws_manager") as mock_ws:
            mock_ws.send_to_user = AsyncMock()
            count = await service.process_pending_reminders()
            assert count == 1
            assert mock_reminder.status == "sent"
            mock_ws.send_to_user.assert_called_once()
            db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_process_pending_reminders_handles_error(self, service, db):
        mock_event = Event(
            id="event-1", user_id="user-1", title="会议",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        mock_reminder = Reminder(
            id="reminder-1", event_id="event-1", user_id="user-1",
            remind_at=datetime.now(timezone.utc), type="push", status="pending",
        )
        mock_reminder.event = mock_event

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_reminder]
        db.query.return_value = mock_query
        db.commit = MagicMock()

        with patch("app.services.reminder_service.ws_manager") as mock_ws:
            mock_ws.send_to_user = AsyncMock(side_effect=Exception("连接失败"))
            count = await service.process_pending_reminders()
            assert count == 0

    @pytest.mark.asyncio
    async def test_process_pending_reminders_empty(self, service, db):
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        db.query.return_value = mock_query
        db.commit = MagicMock()

        count = await service.process_pending_reminders()
        assert count == 0
