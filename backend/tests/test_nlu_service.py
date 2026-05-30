import pytest
from unittest.mock import AsyncMock
from app.services.nlu_service import NLUService


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.parse_calendar_command = AsyncMock(return_value={
        "intent": "create",
        "entities": {
            "title": "开会",
            "date": "2026-06-01",
            "time": "15:00",
            "duration": 60,
            "location": "会议室A",
            "priority": 3,
        },
        "confidence": 0.95,
        "need_clarify": False,
        "clarify_question": None,
    })
    return llm


@pytest.fixture
def service(mock_llm):
    return NLUService(llm=mock_llm)


class TestNLUService:
    @pytest.mark.asyncio
    async def test_parse_command_high_confidence(self, service):
        result = await service.parse_command("明天下午3点开会")
        assert result["intent"] == "create"
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False

    @pytest.mark.asyncio
    async def test_parse_command_returns_response_text(self, service):
        result = await service.parse_command("明天下午3点开会")
        assert "response_text" in result

    @pytest.mark.asyncio
    async def test_parse_command_low_confidence_needs_clarify(self, mock_llm, service):
        mock_llm.parse_calendar_command = AsyncMock(return_value={
            "intent": "create",
            "entities": {"title": "开会"},
            "confidence": 0.4,
            "need_clarify": True,
            "clarify_question": "你想安排在什么时间？",
        })
        result = await service.parse_command("开会")
        assert result["need_clarify"] is True
        assert "clarify_question" in result
