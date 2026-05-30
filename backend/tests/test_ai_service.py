"""AIService 单元测试。"""
from datetime import datetime, date, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from app.models.event import Event
from app.services.ai_service import AIService


# 固定时间基准（2026-06-01 08:00 UTC）
_FROZEN_NOW = datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc)
_FROZEN_DATE = _FROZEN_NOW.date()


def _make_event(user_id: str, title: str, start_hour: int, end_hour: int,
                event_date: date | None = None, priority: int = 3,
                location: str | None = None) -> Event:
    """辅助函数：创建 Event 对象。"""
    d = event_date or _FROZEN_DATE
    return Event(
        id=f"evt-{title}",
        user_id=user_id,
        title=title,
        start_time=datetime(d.year, d.month, d.day, start_hour, 0, tzinfo=timezone.utc),
        end_time=datetime(d.year, d.month, d.day, end_hour, 0, tzinfo=timezone.utc),
        location=location,
        priority=priority,
    )


def _mock_db_with_events(events: list[Event]) -> MagicMock:
    """构造 Mock Session，使 filter/and_ 链式调用返回给定事件列表。"""
    db = MagicMock()
    mock_query = MagicMock()

    # detect_conflicts 使用单次 .filter(and_(...)) → .all()
    # recommend/free_slots 使用 .filter(and_(...)) → .order_by(...) → .all()
    # generate_daily_briefing 使用 .filter(and_(...)) → .order_by(...) → .all()
    mock_filtered = MagicMock()
    mock_filtered.all.return_value = events
    mock_filtered.order_by.return_value = mock_filtered  # order_by 后仍返回自身

    mock_query.filter.return_value = mock_filtered
    db.query.return_value = mock_query
    return db


# ---------------------------------------------------------------------------
# detect_conflicts
# ---------------------------------------------------------------------------

class TestDetectConflicts:
    """AIService.detect_conflicts 测试组。"""

    def test_detect_no_conflicts(self):
        """空数据库应返回空列表。"""
        db = _mock_db_with_events([])
        llm = AsyncMock()
        svc = AIService(db=db, llm=llm)

        start = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc)
        result = svc.detect_conflicts("user-1", start, end)

        assert result == []
        db.query.assert_called_once_with(Event)

    def test_detect_conflict_found(self):
        """存在重叠事件时应返回冲突列表。"""
        user_id = "user-1"
        existing = _make_event(user_id, "已有会议", 9, 11)

        db = _mock_db_with_events([existing])
        llm = AsyncMock()
        svc = AIService(db=db, llm=llm)

        # 新事件 10:00-12:00 与 9:00-11:00 重叠
        start = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
        result = svc.detect_conflicts(user_id, start, end)

        assert len(result) == 1
        assert result[0].title == "已有会议"


# ---------------------------------------------------------------------------
# recommend_free_slots
# ---------------------------------------------------------------------------

class TestRecommendFreeSlots:
    """AIService.recommend_free_slots 测试组。"""

    def test_recommend_empty_day(self):
        """无事件的一天应返回 9:00-18:00 的完整空闲段。"""
        db = _mock_db_with_events([])
        llm = AsyncMock()
        svc = AIService(db=db, llm=llm)

        result = svc.recommend_free_slots("user-1", _FROZEN_DATE, 60)

        assert len(result) == 1
        assert result[0]["duration_minutes"] == 540  # 9 hours = 540 min
        assert "09:00" in result[0]["start"]
        assert "18:00" in result[0]["end"]

    def test_recommend_with_gaps(self):
        """有事件的一天应返回事件之间的空闲段。"""
        user_id = "user-1"
        # 事件：9:00-10:00, 14:00-15:00
        ev1 = _make_event(user_id, "早会", 9, 10, _FROZEN_DATE)
        ev2 = _make_event(user_id, "午会", 14, 15, _FROZEN_DATE)

        db = _mock_db_with_events([ev1, ev2])
        llm = AsyncMock()
        svc = AIService(db=db, llm=llm)

        result = svc.recommend_free_slots(user_id, _FROZEN_DATE, 60)

        # 期望：10:00-14:00 (240min), 15:00-18:00 (180min)
        assert len(result) == 2
        assert result[0]["duration_minutes"] == 240
        assert result[1]["duration_minutes"] == 180

    def test_recommend_filters_short_gaps(self):
        """小于请求时长的间隙不应返回。"""
        user_id = "user-1"
        # 事件：9:00-11:00, 11:30-12:00
        ev1 = _make_event(user_id, "会议A", 9, 11, _FROZEN_DATE)
        ev2 = _make_event(user_id, "会议B", 11, 12, _FROZEN_DATE,
                          location=None)
        # 覆盖 ev2 的时间为 11:30-12:00
        ev2.start_time = datetime(2026, 6, 1, 11, 30, tzinfo=timezone.utc)
        ev2.end_time = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)

        db = _mock_db_with_events([ev1, ev2])
        llm = AsyncMock()
        svc = AIService(db=db, llm=llm)

        result = svc.recommend_free_slots(user_id, _FROZEN_DATE, 60)

        # 11:00-11:30 只有 30 分钟，不满足 60 分钟最小要求
        # 12:00-18:00 有 360 分钟
        assert len(result) == 1
        assert result[0]["duration_minutes"] == 360


# ---------------------------------------------------------------------------
# generate_daily_briefing
# ---------------------------------------------------------------------------

class TestGenerateDailyBriefing:
    """AIService.generate_daily_briefing 异步测试组。"""

    @pytest.mark.asyncio
    @patch("app.services.ai_service.datetime")
    async def test_generate_briefing_with_events(self, mock_dt):
        """有事件时应调用 LLM 生成摘要。"""
        mock_dt.now.return_value = _FROZEN_NOW
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        user_id = "user-1"
        ev = _make_event(user_id, "团队周会", 10, 11, _FROZEN_DATE)

        db = _mock_db_with_events([ev])
        llm = AsyncMock()
        llm.chat.return_value = "今天上午10点有一个团队周会，记得准时参加！"

        svc = AIService(db=db, llm=llm)
        result = await svc.generate_daily_briefing(user_id, "morning")

        assert "团队周会" in result
        llm.chat.assert_called_once()
        # 验证传给 LLM 的消息格式
        call_args = llm.chat.call_args
        messages = call_args[0][0]
        assert isinstance(messages, list)
        assert len(messages) == 2  # system + user

    @pytest.mark.asyncio
    @patch("app.services.ai_service.datetime")
    async def test_generate_briefing_no_events(self, mock_dt):
        """无事件时应返回默认消息，不调用 LLM。"""
        mock_dt.now.return_value = _FROZEN_NOW
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        user_id = "user-1"

        db = _mock_db_with_events([])
        llm = AsyncMock()
        svc = AIService(db=db, llm=llm)

        result = await svc.generate_daily_briefing(user_id, "morning")

        assert "没有" in result or "安排" in result
        llm.chat.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.ai_service.datetime")
    async def test_generate_briefing_evening_uses_tomorrow(self, mock_dt):
        """evening 期间应返回带'明天'的默认消息。"""
        mock_dt.now.return_value = _FROZEN_NOW
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        user_id = "user-1"

        db = _mock_db_with_events([])
        llm = AsyncMock()
        svc = AIService(db=db, llm=llm)

        result = await svc.generate_daily_briefing(user_id, "evening")

        assert "明天" in result
        llm.chat.assert_not_called()
