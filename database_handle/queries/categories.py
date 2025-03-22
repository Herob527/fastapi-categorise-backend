from sqlalchemy import Column
from sqlalchemy.orm import Session

from database_handle.models.categories import Category


def get_one_category(db: Session, name: Column[str] | str) -> Category | None:
    return db.query(Category).filter(Category.name == name).first()


def get_categories_count(db: Session):
    return db.query(Category).count()


def get_all_categories(db: Session):
    return db.query(Category).all()


def remove_category(db: Session, name: str):
    db.query(Category).filter(Category.name == name).delete(synchronize_session=False)
    db.commit()


def create_category(db: Session, category: Category):
    category_exists = get_one_category(db, name=category.name)
    if category_exists:
        return
    db.add(category)
    db.commit()


def update_category(db: Session, category: Category):
    db.query(Category).filter(Category.id == category.id).update(
            {"name": category.name, "id": category.id}, synchronize_session=False
    )
    db.commit()
