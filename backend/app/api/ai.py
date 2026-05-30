from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/parse")
async def parse_command(
    text: str,
    current_user: User = Depends(get_current_user),
):
    # Placeholder for direct NLU parsing
    return {"code": 0, "data": {"text": text}, "message": "请使用 /api/voice/command"}


@router.post("/detect-conflicts")
async def detect_conflicts(
    current_user: User = Depends(get_current_user),
):
    # Placeholder — implemented in phase 8
    return {"code": 0, "data": {"conflicts": []}, "message": "冲突检测功能即将上线"}


@router.post("/recommend-slot")
async def recommend_slot(
    current_user: User = Depends(get_current_user),
):
    # Placeholder — implemented in phase 8
    return {"code": 0, "data": {"slots": []}, "message": "空闲推荐功能即将上线"}


@router.get("/daily-briefing")
async def daily_briefing(
    current_user: User = Depends(get_current_user),
):
    # Placeholder — implemented in phase 8
    return {"code": 0, "data": {"briefing": ""}, "message": "每日摘要功能即将上线"}
