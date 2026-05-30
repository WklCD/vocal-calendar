from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        user = auth_service.register(req.email, req.username, req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"code": 0, "data": UserResponse.from_orm(user), "message": "注册成功"}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        tokens = auth_service.login(req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return {"code": 0, "data": tokens, "message": "登录成功"}


@router.post("/refresh")
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        tokens = auth_service.refresh(req.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return {"code": 0, "data": tokens, "message": "刷新成功"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"code": 0, "data": UserResponse.from_orm(current_user), "message": "ok"}


@router.put("/me")
def update_me(
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    try:
        user = auth_service.update_user(
            current_user.id,
            username=req.username,
            avatar_url=req.avatar_url,
            theme=req.theme,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"code": 0, "data": UserResponse.from_orm(user), "message": "更新成功"}
