from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.category import CategoryCreateRequest, CategoryUpdateRequest, CategoryResponse
from app.services.category_service import CategoryService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    categories = service.get_categories(current_user.id)
    return {"code": 0, "data": [CategoryResponse.model_validate(c) for c in categories], "message": "ok"}


@router.post("")
def create_category(
    req: CategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    category = service.create_category(current_user.id, req.name, req.color, req.icon)
    return {"code": 0, "data": CategoryResponse.model_validate(category), "message": "创建成功"}


@router.put("/{category_id}")
def update_category(
    category_id: str,
    req: CategoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    try:
        category = service.update_category(category_id, current_user.id, name=req.name, color=req.color, icon=req.icon)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"code": 0, "data": CategoryResponse.model_validate(category), "message": "更新成功"}


@router.delete("/{category_id}")
def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    try:
        service.delete_category(category_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"code": 0, "data": None, "message": "删除成功"}
