import json
import httpx
from typing import Any
from app.services.llm.base import BaseLLM
from app.core.config import get_settings


PARSE_PROMPT = """你是一个日历助手。将用户的自然语言解析为JSON。

用户输入: "{text}"

{context_section}

严格按以下JSON格式返回，不要返回其他内容:
{{
    "intent": "create",
    "entities": {{
        "title": "事件名称",
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "duration": 60,
        "location": null,
        "priority": 3
    }},
    "confidence": 0.9,
    "need_clarify": false,
    "clarify_question": null
}}

规则:
- title: 只提取事件名称（如"会议"、"项目讨论"），不要包含时间地点等修饰词
- date: 今天是2026-05-30，根据"明天"、"后天"、"下周X"等推算具体日期
- time: 24小时制，"下午3点"→"15:00"，"上午10点"→"10:00"
- duration: 默认60分钟，除非用户指定了时长
- intent: create/delete/modify/query
- confidence: 如果能识别出事件名称和时间，给0.9以上
- 只要能理解意图，就不要设置need_clarify=true

示例:
输入: "帮我创建明天下午三点的会议"
输出: {{"intent":"create","entities":{{"title":"会议","date":"2026-05-31","time":"15:00","duration":60,"location":null,"priority":3}},"confidence":0.95,"need_clarify":false,"clarify_question":null}}
"""


class MiMoLLM(BaseLLM):
    """小米 MiMo LLM 适配器。"""

    def __init__(self, api_key: str | None = None, model: str = "mimo-v2.5"):
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "MIMO_API_KEY", "")
        self.model = model
        self.base_url = "https://token-plan-cn.xiaomimimo.com/v1"

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
