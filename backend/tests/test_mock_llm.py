import pytest
from app.services.llm.mock import MockLLM


@pytest.fixture
def mock_llm():
    return MockLLM()


class TestMockLLM:
    @pytest.mark.asyncio
    async def test_parse_create_with_date_and_time(self, mock_llm):
        result = await mock_llm.parse_calendar_command("帮我创建明天下午3点的会议")
        assert result["intent"] == "create"
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False
        assert "会议" in result["entities"]["title"]
        assert result["entities"]["date"] is not None
        assert result["entities"]["time"] is not None

    @pytest.mark.asyncio
    async def test_parse_create_today(self, mock_llm):
        result = await mock_llm.parse_calendar_command("今天上午10点开个会")
        assert result["intent"] == "create"
        assert result["entities"]["time"] == "10:00"

    @pytest.mark.asyncio
    async def test_parse_delete(self, mock_llm):
        result = await mock_llm.parse_calendar_command("删除明天的会议")
        assert result["intent"] == "delete"

    @pytest.mark.asyncio
    async def test_parse_query(self, mock_llm):
        result = await mock_llm.parse_calendar_command("我明天有什么安排")
        assert result["intent"] == "query"

    @pytest.mark.asyncio
    async def test_parse_modify(self, mock_llm):
        result = await mock_llm.parse_calendar_command("把明天的会议改到后天")
        assert result["intent"] == "modify"

    @pytest.mark.asyncio
    async def test_parse_low_confidence_needs_clarify(self, mock_llm):
        result = await mock_llm.parse_calendar_command("安排一下")
        assert result["confidence"] < 0.7
        assert result["need_clarify"] is True

    @pytest.mark.asyncio
    async def test_chat_returns_placeholder(self, mock_llm):
        response = await mock_llm.chat([{"role": "user", "content": "hello"}])
        assert "Mock" in response
