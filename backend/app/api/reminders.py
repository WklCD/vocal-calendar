"""提醒 API 路由 - 查询和关闭提醒。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.reminder_service import ReminderService
from app.schemas.reminder import ReminderResponse

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderResponse])
def list_reminders(
    status_filter: str | None = Query(None, alias="status", description="按状态过滤: pending / sent / dismissed"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReminderResponse]:
    """获取当前用户的提醒列表。"""
    service = ReminderService(db)
    reminders = service.get_user_reminders(current_user.id, status=status_filter)
    return [ReminderResponse.model_validate(r) for r in reminders]


@router.put("/{reminder_id}/dismiss", response_model=ReminderResponse)
def dismiss_reminder(
    reminder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderResponse:
    """关闭一个提醒。"""
    service = ReminderService(db)
    try:
        reminder = service.dismiss_reminder(reminder_id, current_user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在",
        )
    return ReminderResponse.model_validate(reminder)
