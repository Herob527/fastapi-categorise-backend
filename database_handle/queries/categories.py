from pydantic import UUID4, BaseModel
from sqlalchemy import Column
from sqlalchemy.orm import Session

from database_handle.models.categories import Categories


class GetOneCategory(BaseModel):
    id: UUID4
    name: str


def get_one_category(db: Session, name: Column[str] | str) -> GetOneCategory | None:
    return db.query(Categories).filter(Categories.name == name).first()


def get_all_categories(db: Session):
    return db.query(Categories).all()


def remove_category(db: Session, id: str):
    db.query(Categories).filter(Categories.id == id).delete(synchronize_session=False)
    db.commit()


def create_category(db: Session, category: Categories):
    category_exists = get_one_category(db, name=category.name)
    if category_exists:
        return
    db.add(category)


def update_category(db: Session, category: Categories):
    db.query(Categories).filter(Categories.id == category.id).update(
        category.dict(), synchronize_session=False
    )
    db.commit()
