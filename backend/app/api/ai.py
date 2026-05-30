"""AI 相关 API 路由：冲突检测、空闲时段推荐、每日摘要、TTS 语音合成。"""

import base64
from datetime import datetime, date

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.event import EventResponse
from app.schemas.voice import TTSRequest
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


@router.post("/tts")
async def text_to_speech(
    req: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    """调用 MiMo TTS API 将文本合成为语音。

    返回 base64 编码的 wav 音频数据。
    """
    settings = get_settings()
    api_key = settings.MIMO_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="MIMO_API_KEY 未配置")

    payload = {
        "model": "mimo-v2.5-tts",
        "messages": [
            {"role": "assistant", "content": req.text},
        ],
        "audio": {
            "format": "wav",
            "voice": req.voice,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "api-key": api_key,
                },
                json=payload,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"MiMo TTS API 返回错误: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"MiMo TTS API 请求失败: {str(e)}")

    data = resp.json()
    try:
        audio_b64 = data["choices"][0]["message"]["audio"]["data"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="MiMo TTS API 返回格式异常")

    return {
        "code": 0,
        "data": {"audio": audio_b64},
        "message": "ok",
    }
