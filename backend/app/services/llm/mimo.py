import json
import httpx
from typing import Any
from app.services.llm.base import BaseLLM
from app.core.config import get_settings


PARSE_PROMPT = """你是一个日历助手，负责将用户的自然语言指令解析为结构化的日历操作。

请分析以下用户输入，返回 JSON 格式的解析结果：

用户输入: "{text}"

{context_section}

请返回以下 JSON 格式（不要返回其他内容）:
{{
    "intent": "create" | "delete" | "modify" | "query",
    "entities": {{
        "title": "事件标题",
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "duration": 分钟数,
        "location": "地点",
        "priority": 1-5
    }},
    "confidence": 0.0-1.0,
    "need_clarify": true/false,
    "clarify_question": "需要追问的问题"
}}

注意:
- 如果用户没有明确指定日期，根据"今天"、"明天"、"后天"、"下周X"等推算
- 如果信息不完整，设置 need_clarify=true 并给出追问问题
- confidence 根据信息完整度和明确程度判断
"""


class MiMoLLM(BaseLLM):
    """小米 MiMo LLM 适配器。"""

    def __init__(self, api_key: str | None = None, model: str = "mimo-v2.5"):
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "MIMO_API_KEY", "")
        self.model = model
        self.base_url = "https://api.xiaomimimo.com/v1"

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_completion_tokens": 1024,
                },
            )
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]
            # MiMo 可能返回 reasoning_content，优先用 content
            return message.get("content") or message.get("reasoning_content", "")

    async def parse_calendar_command(self, text: str, context: dict[str, Any] | None = None) -> dict:
        context_section = ""
        if context:
            context_section = f"之前的对话上下文:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        prompt = PARSE_PROMPT.format(text=text, context_section=context_section)

        messages = [{"role": "user", "content": prompt}]
        response_text = await self.chat(messages)

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        return {
            "intent": "create",
            "entities": {"title": text},
            "confidence": 0.3,
            "need_clarify": True,
            "clarify_question": "抱歉，我没有完全理解你的意思，请再说一次。",
        }
