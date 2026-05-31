import json
import httpx
from typing import Any
from app.services.llm.base import BaseLLM
from app.core.config import get_settings


PARSE_PROMPT = """你是一个日历助手，负责将用户的自然语言指令解析为结构化的日历操作。

请分析以下用户输入，返回 JSON 格式的解析结果：

用户输入: "{text}"

今天的日期: {today}
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

意图判断规则（按优先级）:
- 包含"修改""改到""改为""调整""移到""推迟""提前" → intent="modify"
- 包含"删除""取消""去掉""移除" → intent="delete"
- 包含"查询""有什么""安排""看看""查看""有哪些" → intent="query"
- 其他情况 → intent="create"

字段提取规则:
- title: 只提取事件名称（如"会议""项目讨论"），不要包含时间地点等修饰词
- date: 根据今天日期推算，"明天"=+1天，"后天"=+2天，"下周X"推算具体日期
- time: 24小时制，"下午3点"→"15:00"，"上午10点"→"10:00"，中文数字也要转换
- duration: 默认60分钟，除非用户指定了时长
- confidence: 能识别出意图就给0.8以上；识别出意图+事件名称给0.85以上；再有时间/日期给0.9以上
- 只要能理解意图，就不要设置need_clarify=true
- query指令：title可以为空，date通常必填

示例:
输入: "帮我创建明天下午三点的会议"
输出: {{"intent":"create","entities":{{"title":"会议","date":"{tomorrow}","time":"15:00","duration":60,"location":null,"priority":3}},"confidence":0.95,"need_clarify":false,"clarify_question":null}}

输入: "修改明天的会议到下午五点"
输出: {{"intent":"modify","entities":{{"title":"会议","date":"{tomorrow}","time":"17:00"}},"confidence":0.95,"need_clarify":false,"clarify_question":null}}

输入: "删除明天5点的会议"
输出: {{"intent":"delete","entities":{{"title":"会议","date":"{tomorrow}","time":"17:00"}},"confidence":0.9,"need_clarify":false,"clarify_question":null}}

输入: "明天有什么安排"
输出: {{"intent":"query","entities":{{"title":null,"date":"{tomorrow}"}},"confidence":0.9,"need_clarify":false,"clarify_question":null}}
"""


class QwenLLM(BaseLLM):
    """通义千问 LLM 适配器。"""

    def __init__(self, api_key: str | None = None, model: str = "qwen-turbo"):
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "QWEN_API_KEY", "")
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def parse_calendar_command(self, text: str, context: dict[str, Any] | None = None) -> dict:
        from datetime import datetime, timedelta, timezone

        context_section = ""
        if context:
            context_section = f"之前的对话上下文:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        today = datetime.now(timezone.utc).date()
        tomorrow = (today + timedelta(days=1)).isoformat()
        day_after_tomorrow = (today + timedelta(days=2)).isoformat()

        prompt = PARSE_PROMPT.format(
            text=text,
            context_section=context_section,
            today=today.isoformat(),
            tomorrow=tomorrow,
            day_after_tomorrow=day_after_tomorrow,
        )

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
