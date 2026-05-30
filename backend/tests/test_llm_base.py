import pytest
from abc import ABC
from app.services.llm.base import BaseLLM


class TestBaseLLM:
    def test_is_abstract(self):
        assert issubclass(BaseLLM, ABC)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseLLM()

    def test_has_parse_calendar_command(self):
        assert hasattr(BaseLLM, 'parse_calendar_command')

    def test_has_chat(self):
        assert hasattr(BaseLLM, 'chat')
