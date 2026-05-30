import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.services.event_service import EventService
from app.models.event import Event


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.fixture
def service(db):
    return EventService(db)


class TestCreateEvent:
    def test_create_event(self, service, db):
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        now = datetime.now(timezone.utc)
        event = service.create_event(user_id="user-1", title="测试会议", start_time=now, end_time=now + timedelta(hours=1))
        assert db.add.called
        assert db.commit.called


class TestGetEvents:
    def test_get_events_by_date_range(self, service, db):
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = mock_query
        now = datetime.now(timezone.utc)
        events = service.get_events("user-1", now, now + timedelta(days=7))
        assert isinstance(events, list)


class TestUpdateEvent:
    def test_update_event_title(self, service, db):
        mock_event = Event(id="event-1", user_id="user-1", title="旧标题", start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc) + timedelta(hours=1))
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_event
        db.query.return_value = mock_query
        db.commit = MagicMock()
        db.refresh = MagicMock()
        result = service.update_event("event-1", "user-1", title="新标题")
        assert mock_event.title == "新标题"


class TestDeleteEvent:
    def test_delete_event(self, service, db):
        mock_event = Event(id="event-1", user_id="user-1")
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_event
        db.query.return_value = mock_query
        db.delete = MagicMock()
        db.commit = MagicMock()
        result = service.delete_event("event-1", "user-1")
        assert db.delete.called


class TestSearchEvents:
    def test_search_events(self, service, db):
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = mock_query
        events = service.search_events("user-1", "会议")
        assert isinstance(events, list)
