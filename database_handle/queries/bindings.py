from pydantic.types import UUID4
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased
from database_handle.models.audios import Audio

from database_handle.models.bindings import Binding
from database_handle.models.categories import Category
from database_handle.models.texts import Text

# Create aliases for the tables
BindingAlias = aliased(Binding, name="binding")
CategoryAlias = aliased(Category, name="category")
AudioAlias = aliased(Audio, name="audio")
TextAlias = aliased(Text, name="text")


def get_one_binding(db: Session, id: str):
    return db.query(Binding).filter(Binding.id == id).first()


def get_all_bindings(db: Session, category_name: str | None = None):

    stmt = (
        select(BindingAlias, CategoryAlias, AudioAlias, TextAlias)
        .join(CategoryAlias)
        .join(AudioAlias)
        .join(TextAlias)
    )

    if category_name:
        stmt = stmt.where(CategoryAlias.name == category_name)

    result = db.execute(stmt).fetchall()

    return result


def get_paginated_bindings(db: Session, page: int = 0, limit: int = 20):
    # Construct the select statement
    stmt = (
        select(BindingAlias, CategoryAlias, AudioAlias, TextAlias)
        .join(CategoryAlias)
        .join(AudioAlias)
        .join(TextAlias)
    )

    stmt = stmt.limit(limit).offset(page * limit)

    result = db.execute(stmt).fetchall()

    return result


def get_total_bindings(db: Session):
    return db.query(Binding).count()


def create_binding(db: Session, binding: Binding):
    db.add(binding)


def remove_binding(db: Session, id: UUID4):
    db.query(Binding).filter(Binding.id == id).delete()
    db.commit()
