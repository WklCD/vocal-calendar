from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.share_service import ShareService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/share", tags=["share"])

# In-memory token -> user_id mapping (for demo; use DB in production)
_share_tokens: dict[str, str] = {}


@router.post("/create")
def create_share_link(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ShareService(db)
    token = service.generate_share_token(current_user.id)
    _share_tokens[token] = current_user.id
    return {
        "code": 0,
        "data": {"share_token": token, "url": f"/shared/{token}"},
        "message": "ok",
    }


@router.get("/{share_token}")
def get_shared_calendar(share_token: str, db: Session = Depends(get_db)):
    user_id = _share_tokens.get(share_token)
    if not user_id:
        raise HTTPException(status_code=404, detail="分享链接无效或已过期")
    service = ShareService(db)
    events = service.get_shared_events(user_id)
    return {
        "code": 0,
        "data": [
            {
                "title": e.title,
                "start": e.start_time.isoformat(),
                "end": e.end_time.isoformat(),
                "allDay": e.is_all_day,
                "location": e.location,
            }
            for e in events
        ],
        "message": "ok",
    }
