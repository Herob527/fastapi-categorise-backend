from pydantic.types import UUID4
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import delete, update

from database_handle.models.audios import Audio
from database_handle.models.bindings import Binding, PaginationModel
from database_handle.models.categories import Category
from database_handle.models.texts import Text

# Create aliases for the tables
BindingAlias = aliased(Binding, name="binding")
CategoryAlias = aliased(Category, name="category")
AudioAlias = aliased(Audio, name="audio")
TextAlias = aliased(Text, name="text")


async def get_pagination(db: AsyncSession):
    stmt = select(func.count("*")).select_from(Binding)

    result= (await db.execute(stmt)).scalar() or 0

    return PaginationModel(total=result)


async def get_one_binding(db: AsyncSession, id: str):
    stmt = select(Binding).where(Binding.id == id)

    result = (await db.execute(stmt)).first()

    return result


async def get_all_bindings(db: AsyncSession, category_name: str | None = None):

    stmt = (
        select(BindingAlias, CategoryAlias, AudioAlias, TextAlias)
        .outerjoin(CategoryAlias)
        .join(AudioAlias)
        .join(TextAlias)
    )

    if category_name:
        stmt = stmt.where(CategoryAlias.name == category_name)

    result = (await db.execute(stmt)).all()

    return result


async def get_paginated_bindings(db: AsyncSession, page: int = 0, limit: int = 20):
    # Construct the select statement
    stmt = (
        select(BindingAlias, CategoryAlias, AudioAlias, TextAlias)
        .outerjoin(CategoryAlias)
        .join(AudioAlias)
        .join(TextAlias)
    ).limit(limit).offset(page * limit).order_by(AudioAlias.file_name)

    result = (await db.execute(stmt)).all()

    return result


async def get_total_bindings(db: AsyncSession):
    stmt = select(func.count("*")).select_from(Binding)

    result= (await db.execute(stmt)).scalar() or 0

    return PaginationModel(total=result)


async def create_binding(db: AsyncSession, binding: Binding):
    db.add(binding)


async def remove_binding(db: AsyncSession, id: UUID4):
    stmt = delete(Binding).where(Binding.id == id)
    db.add(stmt)


async def update_binding_category(binding_id: UUID4, category_id: UUID4 | None, db: AsyncSession):
    stmt = update(Binding).where(Binding.id == binding_id).values(category_id=category_id)
    db.add(stmt)
