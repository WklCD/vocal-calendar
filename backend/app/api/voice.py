from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.voice import VoiceCommandRequest, VoiceCommandResponse, VoiceLogResponse, VoiceHelpItem
from app.services.voice_service import VoiceService
from app.services.nlu_service import NLUService
from app.services.llm.factory import create_llm
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/voice", tags=["voice"])


def get_voice_service(db: Session = Depends(get_db)) -> VoiceService:
    llm = create_llm()
    nlu_service = NLUService(llm=llm)
    return VoiceService(db=db, nlu_service=nlu_service)


@router.post("/command")
async def process_command(
    req: VoiceCommandRequest,
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service),
):
    try:
        result = await voice_service.process_command(current_user.id, req.text)
        return {
            "code": 0,
            "data": result,
            "message": result.get("response_text", "已处理"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/logs")
def get_voice_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    llm = create_llm()
    nlu_service = NLUService(llm=llm)
    voice_service = VoiceService(db=db, nlu_service=nlu_service)
    logs = voice_service.get_logs(current_user.id)
    return {
        "code": 0,
        "data": [VoiceLogResponse.from_orm(log) for log in logs],
        "message": "ok",
    }


@router.get("/help")
def get_voice_help():
    llm = create_llm()
    nlu_service = NLUService(llm=llm)
    db = next(get_db())
    voice_service = VoiceService(db=db, nlu_service=nlu_service)
    help_items = voice_service.get_help()
    return {"code": 0, "data": help_items, "message": "ok"}
