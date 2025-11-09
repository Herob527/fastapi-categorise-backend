from pydantic.types import UUID4
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import delete, update

from database_handle.models.audios import Audio, StatusEnum
from database_handle.models.bindings import (
    Binding,
    BindingEntry,
    BindingModel,
    PaginationModel,
)
from database_handle.models.categories import Category
from database_handle.models.texts import Text

# Create aliases for the tables
BindingAlias = aliased(Binding, name="binding")
CategoryAlias = aliased(Category, name="category")
AudioAlias = aliased(Audio, name="audio")
TextAlias = aliased(Text, name="text")


async def get_pagination(db: AsyncSession):
    stmt = select(func.count("*")).select_from(Binding)

    result = (await db.scalar(stmt)) or 0

    return PaginationModel(total=result)


async def get_all_bindings(
    db: AsyncSession, category_name: str | None = None, skip_empty: bool = False
):

    stmt = (
        select(BindingAlias, CategoryAlias, AudioAlias, TextAlias)
        .outerjoin(CategoryAlias)
        .join(AudioAlias)
        .join(TextAlias)
        .where(AudioAlias.audio_status != StatusEnum.waiting)
    )

    if category_name:
        stmt = stmt.where(CategoryAlias.name == category_name)
    if skip_empty:
        stmt = stmt.where(func.trim(TextAlias.text) != "")

    result = (await db.execute(stmt)).all()

    return [
        BindingModel(
            binding=BindingEntry(
                id=row[0].id,
                category_id=row[0].category_id,
                audio_id=row[0].audio_id,
                text_id=row[0].text_id,
            ),
            category=row[1] if row[1] is not None else None,
            audio=row[2],
            text=row[3],
        )
        for row in result
    ]


async def get_paginated_bindings(db: AsyncSession, page: int = 0, limit: int = 20):
    # Construct the select statement
    stmt = (
        (
            select(BindingAlias, CategoryAlias, AudioAlias, TextAlias)
            .outerjoin(CategoryAlias)
            .join(AudioAlias)
            .join(TextAlias)
        )
        .limit(limit)
        .offset(page * limit)
        .order_by(AudioAlias.file_name)
        .where(AudioAlias.audio_status != StatusEnum.waiting)
    )

    result = (await db.execute(stmt)).all()

    # Convert each row to BindingModel
    return [
        BindingModel(
            binding=BindingEntry(
                id=row[0].id,
                category_id=row[0].category_id,
                audio_id=row[0].audio_id,
                text_id=row[0].text_id,
            ),
            category=row[1] if row[1] is not None else None,
            audio=row[2],
            text=row[3],
        )
        for row in result
    ]


async def get_total_bindings(db: AsyncSession):
    stmt = select(func.count("*")).select_from(Binding)

    result = (await db.scalar(stmt)) or 0

    return PaginationModel(total=result)


async def create_binding(db: AsyncSession, binding: Binding):
    db.add(binding)


async def remove_binding(db: AsyncSession, id: UUID4):
    stmt = delete(Binding).where(Binding.id == id)
    await db.execute(stmt)


async def update_binding_category(
    binding_id: UUID4, category_id: UUID4 | None, db: AsyncSession
):
    stmt = (
        update(Binding).where(Binding.id == binding_id).values(category_id=category_id)
    )
    await db.execute(stmt)
