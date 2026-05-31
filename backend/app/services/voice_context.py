import json
from datetime import datetime, timezone
import redis.asyncio as redis
from app.core.config import get_settings


class VoiceContextManager:
    """管理多轮对话上下文，存储在 Redis 中。"""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client
        self.ttl = 300  # 5 分钟过期

    async def _get_redis(self) -> redis.Redis:
        if not self.redis:
            settings = get_settings()
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis

    async def get_context(self, user_id: str) -> dict:
        """获取用户的对话上下文。"""
        r = await self._get_redis()
        data = await r.get(f"voice_session:{user_id}")
        if data:
            return json.loads(data)
        return {
            "last_intent": None,
            "last_entities": None,
            "turn_count": 0,
        }

    async def update_context(
        self, user_id: str, intent: str, entities: dict
    ) -> dict:
        """更新用户的对话上下文。"""
        context = await self.get_context(user_id)
        context["last_intent"] = intent
        context["last_entities"] = entities
        context["turn_count"] += 1
        context["updated_at"] = datetime.now(timezone.utc).isoformat()

        r = await self._get_redis()
        await r.setex(
            f"voice_session:{user_id}",
            self.ttl,
            json.dumps(context, ensure_ascii=False),
        )
        return context

    async def clear_context(self, user_id: str) -> None:
        """清除用户的对话上下文。"""
        r = await self._get_redis()
        await r.delete(f"voice_session:{user_id}")
