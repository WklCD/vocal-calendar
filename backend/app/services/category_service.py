from sqlalchemy.orm import Session
from app.models.category import Category


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, user_id: str, name: str, color: str = "#4285F4", icon: str = "calendar") -> Category:
        category = Category(user_id=user_id, name=name, color=color, icon=icon)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get_categories(self, user_id: str) -> list[Category]:
        return self.db.query(Category).filter(Category.user_id == user_id).order_by(Category.name).all()

    def update_category(self, category_id: str, user_id: str, **kwargs) -> Category:
        category = self.db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
        if not category:
            raise ValueError("分类不存在")
        for key, value in kwargs.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: str, user_id: str) -> bool:
        category = self.db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
        if not category:
            raise ValueError("分类不存在")
        self.db.delete(category)
        self.db.commit()
        return True
