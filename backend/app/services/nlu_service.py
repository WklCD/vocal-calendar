from typing import Any
from app.services.llm.base import BaseLLM
from app.services.voice_context import VoiceContextManager
from datetime import datetime, timedelta, timezone


class NLUService:
    """自然语言理解服务，将用户语音文本解析为结构化指令。"""

    def __init__(self, llm: BaseLLM, context_manager: VoiceContextManager | None = None):
        self.llm = llm
        self.context_manager = context_manager or VoiceContextManager()

    async def parse_command(
        self, text: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """解析用户语音指令。

        Args:
            text: 语音转文字后的文本
            user_id: 用户 ID（用于获取对话上下文）

        Returns:
            解析结果 + 响应文本
        """
        # 获取对话上下文
        context = None
        if user_id:
            context = await self.context_manager.get_context(user_id)

        # 调用 LLM 解析
        result = await self.llm.parse_calendar_command(text, context)

        # 后处理：补充相对日期
        result = self._resolve_relative_dates(result)

        # 生成响应文本
        response_text = self._generate_response(result)
        result["response_text"] = response_text

        # 更新上下文
        if user_id and not result.get("need_clarify"):
            await self.context_manager.update_context(
                user_id, result["intent"], result.get("entities", {})
            )

        return result

    def _resolve_relative_dates(self, result: dict) -> dict:
        """解析相对日期（明天、后天、下周X等）。"""
        entities = result.get("entities", {})
        if not entities.get("date"):
            today = datetime.now(timezone.utc).date()
            title = entities.get("title", "")

            if "明天" in title:
                entities["date"] = (today + timedelta(days=1)).isoformat()
            elif "后天" in title:
                entities["date"] = (today + timedelta(days=2)).isoformat()
            elif "今天" in title:
                entities["date"] = today.isoformat()

            result["entities"] = entities
        return result

    def _generate_response(self, result: dict) -> str:
        """根据解析结果生成自然语言响应。"""
        intent = result.get("intent", "unknown")
        entities = result.get("entities", {})
        confidence = result.get("confidence", 0)

        if result.get("need_clarify"):
            return result.get("clarify_question", "请再说一次？")

        if confidence < 0.7:
            return "抱歉，我没有完全理解你的意思，请再说一次。"

        title = entities.get("title", "事件")
        date = entities.get("date", "")
        time = entities.get("time", "")

        if intent == "create":
            time_str = f" {time}" if time else ""
            date_str = f"{date}{time_str}" if date else ""
            return f"好的，已为你创建：{title}" + (f"，时间：{date_str}" if date_str else "")
        elif intent == "delete":
            return f"好的，已删除：{title}"
        elif intent == "modify":
            return f"好的，已修改：{title}"
        elif intent == "query":
            if date:
                return f"好的，正在查询{date}的安排"
            return "好的，正在查询"

        return "已处理你的请求。"
