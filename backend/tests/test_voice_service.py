"""测试语音指令服务的核心逻辑。

覆盖三个已修复的 bug：
1. 修改指令误创建新事件
2. 删除指令误删同名事件
3. 查询指令无法识别
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.event import Event
from app.models.voice_log import VoiceLog
from app.models.user import User
from app.services.voice_service import VoiceService
from app.services.nlu_service import NLUService
from app.services.llm.mock import MockLLM


# ─── 测试数据库 Fixtures ────────────────────────────────────────────

@pytest.fixture
def db_session():
    """创建内存 SQLite 测试数据库。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_llm():
    return MockLLM()


@pytest.fixture
def nlu_service(mock_llm):
    return NLUService(llm=mock_llm)


@pytest.fixture
def voice_service(db_session, nlu_service):
    return VoiceService(db=db_session, nlu_service=nlu_service)


@pytest.fixture
def sample_events(db_session):
    """创建测试用的示例事件。"""
    user_id = "test-user"
    today = datetime.now(timezone.utc).date()
    tomorrow = today + timedelta(days=1)

    events = [
        Event(
            id="event-1",
            user_id=user_id,
            title="项目讨论",
            start_time=datetime.combine(tomorrow, datetime.min.time().replace(hour=10, minute=0)).replace(tzinfo=timezone.utc),
            end_time=datetime.combine(tomorrow, datetime.min.time().replace(hour=11, minute=0)).replace(tzinfo=timezone.utc),
        ),
        Event(
            id="event-2",
            user_id=user_id,
            title="团队会议",
            start_time=datetime.combine(tomorrow, datetime.min.time().replace(hour=14, minute=0)).replace(tzinfo=timezone.utc),
            end_time=datetime.combine(tomorrow, datetime.min.time().replace(hour=15, minute=0)).replace(tzinfo=timezone.utc),
        ),
        Event(
            id="event-3",
            user_id=user_id,
            title="面试",
            start_time=datetime.combine(tomorrow, datetime.min.time().replace(hour=17, minute=0)).replace(tzinfo=timezone.utc),
            end_time=datetime.combine(tomorrow, datetime.min.time().replace(hour=18, minute=0)).replace(tzinfo=timezone.utc),
        ),
    ]
    for e in events:
        db_session.add(e)
    db_session.commit()
    return events


# ─── MockLLM 测试 ──────────────────────────────────────────────────

class TestMockLLMIntentParsing:
    """测试 MockLLM 的意图解析。"""

    @pytest.mark.asyncio
    async def test_modify_intent_detected(self):
        """测试 '修改明天的会议到下午五点' 能正确识别为 modify 意图。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("修改明天的会议到下午五点")
        assert result["intent"] == "modify"

    @pytest.mark.asyncio
    async def test_delete_intent_detected(self):
        """测试 '删除明天5点的会议' 能正确识别为 delete 意图。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("删除明天5点的会议")
        assert result["intent"] == "delete"

    @pytest.mark.asyncio
    async def test_query_intent_detected(self):
        """测试 '明天有什么安排' 能正确识别为 query 意图。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("明天有什么安排")
        assert result["intent"] == "query"

    @pytest.mark.asyncio
    async def test_create_intent_detected(self):
        """测试 '帮我创建明天下午三点的会议' 能正确识别为 create 意图。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("帮我创建明天下午三点的会议")
        assert result["intent"] == "create"


class TestMockLLMChineseNumberParsing:
    """测试 MockLLM 的中文数字时间解析。"""

    @pytest.mark.asyncio
    async def test_chinese_number_time_afternoon(self):
        """测试 '下午五点' → 17:00。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("修改明天的会议到下午五点")
        assert result["entities"]["time"] == "17:00"

    @pytest.mark.asyncio
    async def test_chinese_number_time_morning(self):
        """测试 '上午九点' → 09:00。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("创建明天上午九点的会议")
        assert result["entities"]["time"] == "09:00"

    @pytest.mark.asyncio
    async def test_chinese_number_time_with_minutes(self):
        """测试 '下午两点半' (中文数字+分钟) → 14:30。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("创建明天下午两点半的会议")
        assert result["entities"]["time"] == "14:30"

    @pytest.mark.asyncio
    async def test_arabic_number_time_afternoon(self):
        """测试 '下午3点' → 15:00。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("创建明天下午3点的会议")
        assert result["entities"]["time"] == "15:00"


class TestMockLLMConfidence:
    """测试 MockLLM 的置信度评分。"""

    @pytest.mark.asyncio
    async def test_query_without_title_high_confidence(self):
        """测试 '明天有什么安排' 无标题时仍有高置信度。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("明天有什么安排")
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False

    @pytest.mark.asyncio
    async def test_modify_with_full_info_high_confidence(self):
        """测试修改指令有完整信息时高置信度。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("修改明天的会议到下午五点")
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False

    @pytest.mark.asyncio
    async def test_delete_with_time_high_confidence(self):
        """测试删除指令有时间信息时高置信度。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("删除明天5点的会议")
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False


class TestMockLLMDateParsing:
    """测试 MockLLM 的日期解析。"""

    @pytest.mark.asyncio
    async def test_tomorrow_date(self):
        """测试 '明天' 日期解析。"""
        llm = MockLLM()
        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()
        result = await llm.parse_calendar_command("明天有什么安排")
        assert result["entities"]["date"] == tomorrow

    @pytest.mark.asyncio
    async def test_day_after_tomorrow_date(self):
        """测试 '后天' 日期解析。"""
        llm = MockLLM()
        today = datetime.now(timezone.utc).date()
        day_after = (today + timedelta(days=2)).isoformat()
        result = await llm.parse_calendar_command("创建后天的会议")
        assert result["entities"]["date"] == day_after

    @pytest.mark.asyncio
    async def test_title_clean_no_date_words(self):
        """测试标题中不包含日期词。"""
        llm = MockLLM()
        result = await llm.parse_calendar_command("修改明天的会议到下午五点")
        title = result["entities"].get("title", "")
        assert "明天" not in title
        assert "下午" not in title


# ─── VoiceService 删除功能测试 ──────────────────────────────────────

class TestDeleteEventPrecision:
    """测试删除事件的精确匹配。"""

    @pytest.mark.asyncio
    async def test_delete_specific_event_by_time(self, voice_service, db_session, sample_events):
        """测试 '删除明天5点的会议' 只删除17:00的面试，不误删其他事件。"""
        user_id = "test-user"
        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()

        entities = {"title": "会议", "date": tomorrow, "time": "17:00"}
        result = await voice_service._delete_event(user_id, entities)

        assert result["status"] == "deleted"
        # 验证只删除了17:00的面试
        deleted_id = result["event_id"]
        remaining = db_session.query(Event).filter(Event.user_id == user_id).all()
        remaining_ids = [e.id for e in remaining]
        assert deleted_id not in remaining_ids
        # 其他事件应仍然存在
        assert len(remaining) == 2

    @pytest.mark.asyncio
    async def test_delete_does_not_delete_all_meetings(self, voice_service, db_session, sample_events):
        """测试删除操作不会删除所有同名事件。"""
        user_id = "test-user"
        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()

        # 先查询明天所有事件数量
        total_before = db_session.query(Event).filter(Event.user_id == user_id).count()

        # 删除特定时间的事件
        entities = {"title": "会议", "date": tomorrow, "time": "17:00"}
        await voice_service._delete_event(user_id, entities)

        # 验证不是全部删除
        total_after = db_session.query(Event).filter(Event.user_id == user_id).count()
        assert total_after == total_before - 1

    @pytest.mark.asyncio
    async def test_delete_by_title_only_matches_first(self, voice_service, db_session, sample_events):
        """测试只按标题匹配时返回第一个匹配项。"""
        user_id = "test-user"

        entities = {"title": "会议"}
        result = await voice_service._delete_event(user_id, entities)
        assert result["status"] == "deleted"


# ─── VoiceService 修改功能测试 ──────────────────────────────────────

class TestModifyEventPrecision:
    """测试修改事件的精确匹配。"""

    @pytest.mark.asyncio
    async def test_modify_event_time(self, voice_service, db_session, sample_events):
        """测试 '修改明天的会议到下午五点' 正确修改时间。"""
        user_id = "test-user"
        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()

        entities = {"title": "会议", "date": tomorrow, "time": "17:00"}
        result = await voice_service._modify_event(user_id, entities)

        assert result["status"] == "modified"
        # 验证修改后的时间
        event = db_session.query(Event).filter(Event.id == result["event_id"]).first()
        assert event.start_time.hour == 17
        assert event.start_time.minute == 0

    @pytest.mark.asyncio
    async def test_modify_creates_no_new_event(self, voice_service, db_session, sample_events):
        """测试修改操作不会创建新事件。"""
        user_id = "test-user"
        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()

        total_before = db_session.query(Event).filter(Event.user_id == user_id).count()

        entities = {"title": "会议", "date": tomorrow, "time": "17:00"}
        await voice_service._modify_event(user_id, entities)

        total_after = db_session.query(Event).filter(Event.user_id == user_id).count()
        assert total_after == total_before  # 数量不变

    @pytest.mark.asyncio
    async def test_modify_preserves_duration(self, voice_service, db_session, sample_events):
        """测试修改时间时保留原事件时长。"""
        user_id = "test-user"
        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()

        # 获取原事件时长
        event = db_session.query(Event).filter(
            Event.user_id == user_id,
            Event.title.ilike("%会议%")
        ).first()
        original_duration = event.end_time - event.start_time

        entities = {"title": "会议", "date": tomorrow, "time": "17:00"}
        result = await voice_service._modify_event(user_id, entities)

        modified_event = db_session.query(Event).filter(Event.id == result["event_id"]).first()
        new_duration = modified_event.end_time - modified_event.start_time
        assert new_duration == original_duration


# ─── VoiceService 查询功能测试 ──────────────────────────────────────

class TestQueryEvents:
    """测试查询事件功能。"""

    @pytest.mark.asyncio
    async def test_query_events_by_date(self, voice_service, db_session, sample_events):
        """测试按日期查询事件。"""
        user_id = "test-user"
        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()

        entities = {"date": tomorrow}
        result = await voice_service._query_events(user_id, entities)

        assert result["status"] == "found"
        assert result["count"] == 3  # 明天有3个事件

    @pytest.mark.asyncio
    async def test_query_events_by_title_and_date(self, voice_service, db_session, sample_events):
        """测试按标题+日期查询事件。"""
        user_id = "test-user"
        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()

        entities = {"title": "会议", "date": tomorrow}
        result = await voice_service._query_events(user_id, entities)

        assert result["status"] == "found"
        assert result["count"] == 1  # 只有1个"团队会议"

    @pytest.mark.asyncio
    async def test_query_all_events(self, voice_service, db_session, sample_events):
        """测试无条件查询所有事件。"""
        user_id = "test-user"

        entities = {}
        result = await voice_service._query_events(user_id, entities)

        assert result["status"] == "found"
        assert result["count"] == 3


# ─── NLU 服务集成测试 ──────────────────────────────────────────────

class TestNLUServiceIntegration:
    """测试 NLU 服务的完整解析流程。"""

    @pytest.mark.asyncio
    async def test_full_parse_modify_command(self, nlu_service):
        """测试完整解析 '修改明天的会议到下午五点'。"""
        result = await nlu_service.parse_command("修改明天的会议到下午五点")
        assert result["intent"] == "modify"
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False
        assert "response_text" in result

    @pytest.mark.asyncio
    async def test_full_parse_delete_command(self, nlu_service):
        """测试完整解析 '删除明天5点的会议'。"""
        result = await nlu_service.parse_command("删除明天5点的会议")
        assert result["intent"] == "delete"
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False

    @pytest.mark.asyncio
    async def test_full_parse_query_command(self, nlu_service):
        """测试完整解析 '明天有什么安排'。"""
        result = await nlu_service.parse_command("明天有什么安排")
        assert result["intent"] == "query"
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False
        assert result["entities"].get("date") is not None

    @pytest.mark.asyncio
    async def test_full_parse_create_command(self, nlu_service):
        """测试完整解析 '帮我创建明天下午三点的会议'。"""
        result = await nlu_service.parse_command("帮我创建明天下午三点的会议")
        assert result["intent"] == "create"
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False


# ─── 回归测试：确保原有功能不受影响 ──────────────────────────────────

class TestRegression:
    """回归测试。"""

    @pytest.mark.asyncio
    async def test_create_event_still_works(self, voice_service, db_session):
        """测试创建事件功能不受影响。"""
        user_id = "test-user"
        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()

        entities = {"title": "新会议", "date": tomorrow, "time": "15:00", "duration": 60}
        result = await voice_service._create_event(user_id, entities)

        assert result["status"] == "created"
        event = db_session.query(Event).filter(Event.id == result["event_id"]).first()
        assert event is not None
        assert event.title == "新会议"

    @pytest.mark.asyncio
    async def test_modify_nonexistent_event_returns_not_found(self, voice_service, db_session):
        """测试修改不存在的事件返回 not_found。"""
        user_id = "test-user"
        entities = {"title": "不存在的事件", "date": "2099-01-01", "time": "10:00"}
        result = await voice_service._modify_event(user_id, entities)
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_event_returns_not_found(self, voice_service, db_session):
        """测试删除不存在的事件返回 not_found。"""
        user_id = "test-user"
        entities = {"title": "不存在的事件", "date": "2099-01-01", "time": "10:00"}
        result = await voice_service._delete_event(user_id, entities)
        assert result["status"] == "not_found"
