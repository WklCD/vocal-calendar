from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.schemas.event import EventCreateRequest, EventUpdateRequest, EventResponse
from app.services.event_service import EventService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
def get_events(
    start: datetime = Query(...),
    end: datetime = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    events = service.get_events(current_user.id, start, end)
    return {"code": 0, "data": [EventResponse.model_validate(e) for e in events], "message": "ok"}


@router.post("")
def create_event(
    req: EventCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    event = service.create_event(
        user_id=current_user.id,
        title=req.title,
        description=req.description,
        start_time=req.start_time,
        end_time=req.end_time,
        is_all_day=req.is_all_day,
        location=req.location,
        category_id=req.category_id,
        priority=req.priority,
        color=req.color,
        recurrence_rule=req.recurrence_rule,
    )
    return {"code": 0, "data": EventResponse.model_validate(event), "message": "创建成功"}


@router.get("/search")
def search_events(
    q: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    events = service.search_events(current_user.id, q)
    return {"code": 0, "data": [EventResponse.model_validate(e) for e in events], "message": "ok"}


@router.get("/{event_id}")
def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    event = service.get_event_by_id(event_id, current_user.id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    return {"code": 0, "data": EventResponse.model_validate(event), "message": "ok"}


@router.put("/{event_id}")
def update_event(
    event_id: str,
    req: EventUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    try:
        event = service.update_event(
            event_id,
            current_user.id,
            title=req.title,
            description=req.description,
            start_time=req.start_time,
            end_time=req.end_time,
            is_all_day=req.is_all_day,
            location=req.location,
            category_id=req.category_id,
            priority=req.priority,
            color=req.color,
            recurrence_rule=req.recurrence_rule,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"code": 0, "data": EventResponse.model_validate(event), "message": "更新成功"}


@router.delete("/{event_id}")
def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    try:
        service.delete_event(event_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"code": 0, "data": None, "message": "删除成功"}
