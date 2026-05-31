import re
from datetime import datetime, timedelta, timezone
from typing import Any
from app.services.llm.base import BaseLLM

# 中文数字到阿拉伯数字的映射
CHINESE_NUMS = {
    "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12,
}


def _chinese_to_num(s: str) -> int | None:
    """将中文数字字符串转为整数。"""
    if s in CHINESE_NUMS:
        return CHINESE_NUMS[s]
    # 处理 "十X" 格式
    if s.startswith("十") and len(s) == 2:
        tail = s[1]
        if tail in CHINESE_NUMS:
            return 10 + CHINESE_NUMS[tail]
    return None


class MockLLM(BaseLLM):
    """开发模式 Mock LLM，用正则解析常见指令，不需要 API Key。"""

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return "Mock LLM 不支持通用对话，请配置真实 LLM。"

    async def parse_calendar_command(self, text: str, context: dict[str, Any] | None = None) -> dict:
        """用正则匹配解析中文日历指令。"""
        today = datetime.now(timezone.utc).date()

        # 解析意图
        intent = "create"
        if any(w in text for w in ["删除", "取消", "去掉", "移除"]):
            intent = "delete"
        elif any(w in text for w in ["查询", "有什么", "安排", "看看", "查看", "有哪些"]):
            intent = "query"
        elif any(w in text for w in ["修改", "改到", "改为", "调整", "移到", "推迟", "提前"]):
            intent = "modify"

        # 解析日期
        date_str = None
        if "今天" in text:
            date_str = today.isoformat()
        elif "明天" in text:
            date_str = (today + timedelta(days=1)).isoformat()
        elif "后天" in text:
            date_str = (today + timedelta(days=2)).isoformat()
        elif "大后天" in text:
            date_str = (today + timedelta(days=3)).isoformat()
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

        # 解析时间（支持中文数字和阿拉伯数字）
        time_str = None

        # 模式1: "下午/上午 + 中文数字 + 点半"（如"下午两点半"）
        m = re.search(r'(下午|晚上|傍晚)([一二两三四五六七八九十]+)点半', text)
        if m:
            hour = _chinese_to_num(m.group(2))
            if hour is not None:
                if hour < 12:
                    hour += 12
                time_str = f"{hour:02d}:30"

        # 模式2: "下午/上午 + 中文数字 + 点 + 分钟"（如"下午三点二十分"）
        if not time_str:
            m = re.search(r'(下午|晚上|傍晚)([一二两三四五六七八九十]+)点(\d{1,2})分?', text)
            if m:
                hour = _chinese_to_num(m.group(2))
                if hour is not None:
                    minute = int(m.group(3))
                    if hour < 12:
                        hour += 12
                    time_str = f"{hour:02d}:{minute:02d}"

        # 模式3: "下午/上午 + 中文数字 + 点"（如"下午五点"）
        if not time_str:
            m = re.search(r'(下午|晚上|傍晚)([一二两三四五六七八九十]+)点', text)
            if m:
                hour = _chinese_to_num(m.group(2))
                if hour is not None:
                    if hour < 12:
                        hour += 12
                    time_str = f"{hour:02d}:00"

        # 模式4: "下午/上午 + 阿拉伯数字 + 点半"（如"下午3点半"）
        if not time_str:
            m = re.search(r'(下午|晚上|傍晚)(\d{1,2})点半', text)
            if m:
                hour = int(m.group(2))
                if hour < 12:
                    hour += 12
                time_str = f"{hour:02d}:30"

        # 模式5: "下午/上午 + 阿拉伯数字 + 点 + 分钟"（如"下午3点20分"）
        if not time_str:
            m = re.search(r'(下午|晚上|傍晚)(\d{1,2})点(\d{1,2})分?', text)
            if m:
                hour = int(m.group(2))
                minute = int(m.group(3))
                if hour < 12:
                    hour += 12
                time_str = f"{hour:02d}:{minute:02d}"

        # 模式6: "下午/上午 + 阿拉伯数字 + 点"（如"下午3点"）
        if not time_str:
            m = re.search(r'(下午|晚上|傍晚)(\d{1,2})点', text)
            if m:
                hour = int(m.group(2))
                if hour < 12:
                    hour += 12
                time_str = f"{hour:02d}:00"

        # 模式7: "数字点半"（阿拉伯数字，带可选的上午/下午前缀）
        if not time_str:
            m = re.search(r'(上午|早上|早晨|下午|晚上|傍晚)?(\d{1,2})点半', text)
            if m:
                hour = int(m.group(2))
                if m.group(1) in ("下午", "晚上", "傍晚") or (m.group(1) is None and "下午" in text):
                    if hour < 12:
                        hour += 12
                time_str = f"{hour:02d}:30"

        # 模式8: "数字点"（阿拉伯数字，带可选的上午/下午前缀）
        if not time_str:
            m = re.search(r'(上午|早上|早晨|下午|晚上|傍晚)?(\d{1,2})点(\d{1,2})?分?', text)
            if m:
                hour = int(m.group(2))
                minute = int(m.group(3)) if m.group(3) else 0
                if m.group(1) in ("下午", "晚上", "傍晚") or (m.group(1) is None and "下午" in text):
                    if hour < 12:
                        hour += 12
                time_str = f"{hour:02d}:{minute:02d}"

        # 模式9: "中文数字点半"（无上午/下午前缀，如"两点半"）
        if not time_str:
            m = re.search(r'([一二两三四五六七八九十]+)点半', text)
            if m:
                hour = _chinese_to_num(m.group(1))
                if hour is not None:
                    if "下午" in text and hour < 12:
                        hour += 12
                    time_str = f"{hour:02d}:30"

        # 模式10: "中文数字点"（无上午/下午前缀，如"五点"）
        if not time_str:
            m = re.search(r'([一二两三四五六七八九十]+)点(\d{1,2})?分?', text)
            if m:
                hour = _chinese_to_num(m.group(1))
                if hour is not None:
                    minute = int(m.group(2)) if m.group(2) else 0
                    if "下午" in text and hour < 12:
                        hour += 12
                    time_str = f"{hour:02d}:{minute:02d}"

        # 模式5: HH:MM 格式
        if not time_str:
            m = re.search(r'(\d{1,2}):(\d{2})', text)
            if m:
                time_str = f"{int(m.group(1)):02d}:{m.group(2)}"

        # 解析标题（提取关键名词）
        title = None
        # 去掉时间/意图相关词后提取
        cleaned = text
        stop_words = [
            "今天", "明天", "后天", "大后天", "上午", "下午", "早上", "晚上", "傍晚",
            "帮我", "创建", "新建", "添加", "安排", "设一个", "删除", "取消", "查询",
            "有什么", "修改", "改到", "改为", "调整", "移到", "推迟", "提前",
            "一下", "一下吧", "提醒我", "看看", "查看", "有哪些", "去掉", "移除",
        ]
        for w in stop_words:
            cleaned = cleaned.replace(w, "")
        # 去掉日期
        m = re.search(r'(\d{1,2})月', cleaned)
        if m:
            cleaned = re.sub(r'\d{1,2}月\d{1,2}[日号]?', '', cleaned)
        # 去掉时间（阿拉伯数字）
        cleaned = re.sub(r'\d{1,2}[点:]\d{0,2}分?', '', cleaned)
        # 去掉时间（中文数字）
        cleaned = re.sub(r'[一二两三四五六七八九十]+点\d{0,2}分?', '', cleaned)
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

        entities = {}
        if title:
            entities["title"] = title
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
        has_title = title is not None

        confidence = 0.5
        if has_title:
            confidence += 0.2
        if has_date:
            confidence += 0.15
        if has_time:
            confidence += 0.15

        # query 指令不需要 title 也有较高置信度
        if intent == "query" and has_date and not has_title:
            confidence = max(confidence, 0.85)

        need_clarify = confidence < 0.7
        clarify_question = None
        if need_clarify:
            if not has_date and not has_time:
                clarify_question = "请问你想安排在什么时间？"
            elif not has_title:
                clarify_question = "请问这个事件的标题是什么？"

        return {
            "intent": intent,
            "entities": entities,
            "confidence": min(confidence, 1.0),
            "need_clarify": need_clarify,
            "clarify_question": clarify_question,
        }
