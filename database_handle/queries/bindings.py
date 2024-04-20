from pydantic.types import UUID4
from sqlalchemy.orm import Session
from database_handle.models.audios import Audio

from database_handle.models.bindings import Binding
from database_handle.models.categories import Category
from database_handle.models.texts import Text


def get_one_binding(db: Session, id: str):
    return db.query(Binding).filter(Binding.id == id).first()


def get_all_bindings(db: Session, category_name: str | None = None):
    query = (
        db.query(Binding, Category, Audio, Text).join(Category).join(Audio).join(Text)
    )
    if category_name:
        query = query.where(Category.name == category_name)
    return query.all()


def get_paginated_bindings(db: Session, page: int = 0, limit: int = 20):
    return db.query(Binding).limit(limit).offset(page * limit).all()


def get_total_bindings(db: Session):
    return db.query(Binding).count()


def create_binding(db: Session, binding: Binding):
    db.add(binding)


def remove_binding(db: Session, id: UUID4):
    db.query(Binding).filter(Binding.id == id).delete()
    db.commit()
