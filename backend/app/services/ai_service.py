"""AI 服务：冲突检测、空闲推荐、每日摘要。"""
from datetime import datetime, date, timedelta, timezone

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.event import Event
from app.services.llm.base import BaseLLM


# 工作时间范围（默认）
_WORK_START_HOUR = 9
_WORK_END_HOUR = 18


class AIService:
    """AI 日历助手服务。

    提供事件冲突检测、空闲时段推荐、每日/每晚摘要生成。
    """

    def __init__(self, db: Session, llm: BaseLLM):
        self.db = db
        self.llm = llm

    # ------------------------------------------------------------------
    # 冲突检测
    # ------------------------------------------------------------------

    def detect_conflicts(self, user_id: str, start_time: datetime, end_time: datetime) -> list[Event]:
        """查找与给定时间段重叠的已有事件。

        重叠条件：existing.start < new.end AND existing.end > new.start

        Args:
            user_id: 用户 ID
            start_time: 新事件开始时间
            end_time: 新事件结束时间

        Returns:
            与指定时间段冲突的事件列表
        """
        return (
            self.db.query(Event)
            .filter(
                and_(
                    Event.user_id == user_id,
                    Event.start_time < end_time,
                    Event.end_time > start_time,
                )
            )
            .all()
        )

    # ------------------------------------------------------------------
    # 空闲时段推荐
    # ------------------------------------------------------------------

    def recommend_free_slots(
        self,
        user_id: str,
        target_date: date,
        duration_minutes: int = 60,
    ) -> list[dict]:
        """在工作时间（9:00-18:00）内查找满足最小时长的空闲时段。

        Args:
            user_id: 用户 ID
            target_date: 目标日期
            duration_minutes: 最小空闲时长（分钟），默认 60

        Returns:
            空闲时段列表，每项包含 start/end (ISO 字符串) 和 duration_minutes
        """
        tz = timezone.utc
        work_start = datetime(
            target_date.year, target_date.month, target_date.day,
            _WORK_START_HOUR, 0, tzinfo=tz,
        )
        work_end = datetime(
            target_date.year, target_date.month, target_date.day,
            _WORK_END_HOUR, 0, tzinfo=tz,
        )

        # 查询当天工作时间内的事件，按开始时间排序
        events = (
            self.db.query(Event)
            .filter(
                and_(
                    Event.user_id == user_id,
                    Event.start_time < work_end,
                    Event.end_time > work_start,
                )
            )
            .order_by(Event.start_time)
            .all()
        )

        free_slots: list[dict] = []
        cursor = work_start

        for event in events:
            # 将事件边界裁剪到工作时间范围
            ev_start = max(event.start_time, work_start)
            ev_end = min(event.end_time, work_end)

            if cursor < ev_start:
                gap = (ev_start - cursor).total_seconds() / 60
                if gap >= duration_minutes:
                    free_slots.append({
                        "start": cursor.isoformat(),
                        "end": ev_start.isoformat(),
                        "duration_minutes": int(gap),
                    })
            cursor = max(cursor, ev_end)

        # 处理最后一个事件到下班之间的间隙
        if cursor < work_end:
            gap = (work_end - cursor).total_seconds() / 60
            if gap >= duration_minutes:
                free_slots.append({
                    "start": cursor.isoformat(),
                    "end": work_end.isoformat(),
                    "duration_minutes": int(gap),
                })

        return free_slots

    # ------------------------------------------------------------------
    # 每日摘要
    # ------------------------------------------------------------------

    async def generate_daily_briefing(self, user_id: str, period: str = "morning") -> str:
        """使用 LLM 生成每日事件摘要。

        Args:
            user_id: 用户 ID
            period: "morning"（查询今天）或 "evening"（查询明天）

        Returns:
            自然语言摘要文本
        """
        tz = timezone.utc
        today = datetime.now(tz).date()

        if period == "evening":
            target_date = today + timedelta(days=1)
        else:
            target_date = today

        work_start = datetime(
            target_date.year, target_date.month, target_date.day,
            _WORK_START_HOUR, 0, tzinfo=tz,
        )
        work_end = datetime(
            target_date.year, target_date.month, target_date.day,
            _WORK_END_HOUR, 0, tzinfo=tz,
        )

        events = (
            self.db.query(Event)
            .filter(
                and_(
                    Event.user_id == user_id,
                    Event.start_time < work_end,
                    Event.end_time > work_start,
                )
            )
            .order_by(Event.start_time)
            .all()
        )

        # 无事件时直接返回默认消息
        if not events:
            if period == "evening":
                return "明天没有安排，可以好好休息一下。"
            return "今天没有安排，享受自由的一天吧！"

        # 构建事件列表文本
        event_lines: list[str] = []
        for ev in events:
            start_str = ev.start_time.strftime("%H:%M")
            end_str = ev.end_time.strftime("%H:%M")
            line = f"- {start_str}-{end_str} {ev.title}"
            if ev.location:
                line += f"（{ev.location}）"
            event_lines.append(line)

        event_list_text = "\n".join(event_lines)

        date_label = "今天" if period == "morning" else "明天"

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个友善的语音日历助手。请根据用户当天的日程安排，"
                    "生成一段简洁自然的摘要，提醒用户注意事项。"
                    "语气亲切、鼓励，使用中文。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"以下是我{date_label}的日程安排：\n\n"
                    f"{event_list_text}\n\n"
                    f"请帮我生成一段简短的{date_label}日程摘要。"
                ),
            },
        ]

        return await self.llm.chat(messages)
