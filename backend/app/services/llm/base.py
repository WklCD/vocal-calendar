from abc import ABC, abstractmethod
from typing import Any


class BaseLLM(ABC):
    """LLM 抽象基类，所有 LLM 适配器必须实现此接口。"""

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """通用对话接口。

        Args:
            messages: 对话消息列表，格式 [{"role": "user", "content": "..."}]

        Returns:
            LLM 回复文本
        """
        pass

    @abstractmethod
    async def parse_calendar_command(self, text: str, context: dict[str, Any] | None = None) -> dict:
        """自然语言 → 结构化日历指令。

        Args:
            text: 用户输入的自然语言文本
            context: 多轮对话上下文（可选）

        Returns:
            结构化指令，格式:
            {
                "intent": "create" | "delete" | "modify" | "query",
                "entities": {
                    "title": str,
                    "date": str (YYYY-MM-DD),
                    "time": str (HH:MM),
                    "duration": int (minutes),
                    "location": str,
                    "priority": int (1-5)
                },
                "confidence": float (0-1),
                "need_clarify": bool,
                "clarify_question": str | None
            }
        """
        pass
