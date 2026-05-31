import re
from datetime import datetime, timedelta, timezone
from typing import Any
from app.services.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """开发模式 Mock LLM，用正则解析常见指令，不需要 API Key。"""

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return "Mock LLM 不支持通用对话，请配置真实 LLM。"

    async def parse_calendar_command(self, text: str, context: dict[str, Any] | None = None) -> dict:
        """用正则匹配解析中文日历指令。"""
        today = datetime.now(timezone.utc).date()

        # 解析意图
        intent = "create"
        if any(w in text for w in ["删除", "取消", "去掉"]):
            intent = "delete"
        elif any(w in text for w in ["查询", "有什么", "安排", "看看"]):
            intent = "query"
        elif any(w in text for w in ["修改", "改到", "改为", "调整"]):
            intent = "modify"

        # 解析日期
        date_str = None
        if "今天" in text:
            date_str = today.isoformat()
        elif "明天" in text:
            date_str = (today + timedelta(days=1)).isoformat()
        elif "后天" in text:
            date_str = (today + timedelta(days=2)).isoformat()
        else:
            # 匹配 "6月1日", "6月1号", "06-01" 等
            m = re.search(r'(\d{1,2})月(\d{1,2})[日号]?', text)
            if m:
                month, day = int(m.group(1)), int(m.group(2))
                year = today.year
                try:
                    date_str = datetime(year, month, day).date().isoformat()
                except ValueError:
                    pass
            if not date_str:
                m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
                if m:
                    date_str = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

        # 解析时间
        time_str = None
        m = re.search(r'(上午|早上|早晨)?(\d{1,2})点(\d{1,2})?分?', text)
        if m:
            hour = int(m.group(2))
            minute = int(m.group(3)) if m.group(3) else 0
            if m.group(1) == "下午" or (m.group(1) is None and "下午" in text):
                if hour < 12:
                    hour += 12
            time_str = f"{hour:02d}:{minute:02d}"
        if not time_str:
            m = re.search(r'下午(\d{1,2})点', text)
            if m:
                hour = int(m.group(1)) + 12
                time_str = f"{hour:02d}:00"
        if not time_str:
            m = re.search(r'(\d{1,2}):(\d{2})', text)
            if m:
                time_str = f"{int(m.group(1)):02d}:{m.group(2)}"

        # 解析标题（提取关键名词）
        title = "新事件"
        # 去掉时间相关词后提取
        cleaned = text
        for w in ["今天", "明天", "后天", "上午", "下午", "早上", "帮我", "创建", "新建",
                   "添加", "安排", "设一个", "删除", "取消", "查询", "有什么", "修改",
                   "一下", "一下吧", "提醒我"]:
            cleaned = cleaned.replace(w, "")
        m = re.search(r'(\d{1,2})月', cleaned)
        if m:
            cleaned = re.sub(r'\d{1,2}月\d{1,2}[日号]?', '', cleaned)
        cleaned = re.sub(r'\d{1,2}[点:]\d{0,2}分?', '', cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            title = cleaned[:20]  # 截取前20字

        # 解析时长
        duration = 60
        m = re.search(r'(\d+)小时', text)
        if m:
            duration = int(m.group(1)) * 60
        m = re.search(r'(\d+)分钟', text)
        if m:
            duration = int(m.group(1))

        # 解析地点
        location = None
        m = re.search(r'在(.+?)(?:开|举|进行|的|$)', text)
        if m:
            location = m.group(1).strip()

        entities = {"title": title}
        if date_str:
            entities["date"] = date_str
        if time_str:
            entities["time"] = time_str
        entities["duration"] = duration
        if location:
            entities["location"] = location

        # 判断置信度
        has_date = date_str is not None
        has_time = time_str is not None
        has_title = title != "新事件"
        confidence = 0.5
        if has_title:
            confidence += 0.2
        if has_date:
            confidence += 0.15
        if has_time:
            confidence += 0.15

        need_clarify = confidence < 0.7
        clarify_question = None
        if need_clarify:
            if not has_date and not has_time:
                clarify_question = "请问你想安排在什么时间？"
            elif not has_title or title == "新事件":
                clarify_question = "请问这个事件的标题是什么？"

        return {
            "intent": intent,
            "entities": entities,
            "confidence": min(confidence, 1.0),
            "need_clarify": need_clarify,
            "clarify_question": clarify_question,
        }
