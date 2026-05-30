from sqlalchemy.orm import Session
from app.models.voice_log import VoiceLog
from app.services.nlu_service import NLUService
from app.models.event import Event
from datetime import datetime, timedelta, timezone


class VoiceService:
    """处理语音指令的完整流程。"""

    def __init__(self, db: Session, nlu_service: NLUService):
        self.db = db
        self.nlu_service = nlu_service

    async def process_command(self, user_id: str, text: str) -> dict:
        """处理语音指令的完整流程。

        1. NLU 解析
        2. 执行动作
        3. 记录日志
        4. 返回结果
        """
        # 1. NLU 解析
        result = await self.nlu_service.parse_command(text, user_id)

        # 2. 执行动作（如果不需要追问且置信度够高）
        if not result.get("need_clarify") and result.get("confidence", 0) >= 0.7:
            action_result = await self._execute_action(user_id, result)
            result["action_result"] = action_result

        # 3. 记录日志
        log = VoiceLog(
            user_id=user_id,
            raw_text=text,
            parsed_intent=result.get("intent"),
            parsed_entities=result.get("entities"),
            response_text=result.get("response_text"),
        )
        self.db.add(log)
        self.db.commit()

        return result

    async def _execute_action(self, user_id: str, result: dict) -> dict:
        """根据解析结果执行对应动作。"""
        intent = result.get("intent")
        entities = result.get("entities", {})

        if intent == "create":
            return await self._create_event(user_id, entities)
        elif intent == "delete":
            return await self._delete_event(user_id, entities)
        elif intent == "query":
            return await self._query_events(user_id, entities)

        return {"status": "noop"}

    async def _create_event(self, user_id: str, entities: dict) -> dict:
        """创建事件。"""
        title = entities.get("title", "新事件")
        date_str = entities.get("date")
        time_str = entities.get("time")
        duration = entities.get("duration", 60)

        if date_str and time_str:
            start = datetime.fromisoformat(f"{date_str}T{time_str}:00")
        elif date_str:
            start = datetime.fromisoformat(f"{date_str}T09:00:00")
        else:
            start = datetime.now(timezone.utc).replace(second=0, microsecond=0)

        # Apply timezone
        start = start.replace(tzinfo=timezone.utc)
        end = start + timedelta(minutes=duration)

        event = Event(
            user_id=user_id,
            title=title,
            start_time=start,
            end_time=end,
            location=entities.get("location"),
            priority=entities.get("priority", 3),
        )
        self.db.add(event)
        self.db.commit()

        return {"status": "created", "event_id": event.id}

    async def _delete_event(self, user_id: str, entities: dict) -> dict:
        """删除事件（按标题模糊匹配）。"""
        title = entities.get("title", "")
        event = (
            self.db.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.title.ilike(f"%{title}%"),
            )
            .first()
        )
        if event:
            self.db.delete(event)
            self.db.commit()
            return {"status": "deleted", "event_id": event.id}
        return {"status": "not_found"}

    async def _query_events(self, user_id: str, entities: dict) -> dict:
        """查询事件。"""
        title = entities.get("title", "")
        date_str = entities.get("date")

        query = self.db.query(Event).filter(Event.user_id == user_id)

        if title:
            query = query.filter(Event.title.ilike(f"%{title}%"))
        if date_str:
            date = datetime.fromisoformat(date_str)
            query = query.filter(
                Event.start_time >= date,
                Event.start_time < date + timedelta(days=1),
            )

        events = query.order_by(Event.start_time).all()
        return {
            "status": "found",
            "count": len(events),
            "events": [
                {"id": e.id, "title": e.title, "start": e.start_time.isoformat()}
                for e in events
            ],
        }

    def get_logs(self, user_id: str, limit: int = 50) -> list[VoiceLog]:
        """获取语音指令历史。"""
        return (
            self.db.query(VoiceLog)
            .filter(VoiceLog.user_id == user_id)
            .order_by(VoiceLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_help(self) -> list[dict]:
        """获取语音指令帮助列表。"""
        return [
            {"command": "创建事件", "example": "帮我创建明天下午3点的会议", "description": "创建新的日历事件"},
            {"command": "删除事件", "example": "删除明天的会议", "description": "删除指定事件"},
            {"command": "查询事件", "example": "我明天有什么安排", "description": "查询指定时间的事件"},
            {"command": "修改事件", "example": "把明天的会议改到后天", "description": "修改已有事件"},
        ]
