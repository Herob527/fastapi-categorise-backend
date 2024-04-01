from sqlalchemy import Column
from sqlalchemy.orm import Session

from database_handle.models.categories import Categories


def get_one_category(db: Session, name: Column[str] | str) -> Categories | None:
    return db.query(Categories).filter(Categories.name == name).first()


def get_categories_count(db: Session):
    return db.query(Categories).count()


def get_all_categories(db: Session):
    return db.query(Categories).all()


def remove_category(db: Session, name: str):
    db.query(Categories).filter(Categories.name == name).delete(
        synchronize_session=False
    )
    db.commit()


def create_category(db: Session, category: Categories):
    category_exists = get_one_category(db, name=category.name)
    if category_exists:
        return
    db.add(category)
    db.commit()


def update_category(db: Session, category: Categories):
    db.query(Categories).filter(Categories.id == category.id).update(
        category.dict(), synchronize_session=False
    )
    db.commit()
