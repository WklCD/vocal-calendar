"""AI 相关 API 路由：冲突检测、空闲时段推荐、每日摘要。"""

from datetime import datetime, date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.event import EventResponse
from app.services.ai_service import AIService
from app.services.llm.factory import create_llm

router = APIRouter(prefix="/api/ai", tags=["ai"])


def get_ai_service(db: Session = Depends(get_db)) -> AIService:
    """创建 AIService 依赖，注入数据库会话和 LLM 实例。"""
    llm = create_llm()
    return AIService(db=db, llm=llm)


@router.post("/detect-conflicts")
async def detect_conflicts(
    start_time: datetime = Query(..., description="新事件开始时间（ISO 格式）"),
    end_time: datetime = Query(..., description="新事件结束时间（ISO 格式）"),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    """检测与指定时间段重叠的已有事件。

    传入新事件的 start_time 和 end_time，返回所有与之冲突的事件列表。
    """
    conflicts = ai_service.detect_conflicts(
        user_id=current_user.id,
        start_time=start_time,
        end_time=end_time,
    )
    return {
        "code": 0,
        "data": {
            "conflicts": [EventResponse.model_validate(e).model_dump() for e in conflicts],
        },
        "message": "ok",
    }


@router.post("/recommend-slot")
async def recommend_slot(
    target_date: date = Query(..., description="目标日期（YYYY-MM-DD）"),
    duration_minutes: int = Query(60, ge=15, le=480, description="最小时长（分钟）"),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    """推荐指定日期的空闲时段。

    在工作时间（9:00-18:00）内查找满足最小持续时长的空闲时间段。
    """
    slots = ai_service.recommend_free_slots(
        user_id=current_user.id,
        target_date=target_date,
        duration_minutes=duration_minutes,
    )
    return {
        "code": 0,
        "data": {"slots": slots},
        "message": "ok",
    }


@router.get("/daily-briefing")
async def daily_briefing(
    period: str = Query(
        "morning",
        pattern="^(morning|evening)$",
        description="时段：morning（今日摘要）或 evening（明日摘要）",
    ),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    """生成每日日程摘要。

    morning 返回当天日程摘要，evening 返回明日日程摘要。
    """
    briefing = await ai_service.generate_daily_briefing(
        user_id=current_user.id,
        period=period,
    )
    return {
        "code": 0,
        "data": {"briefing": briefing},
        "message": "ok",
    }
