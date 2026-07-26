from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from pydantic.types import UUID4
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import delete, update

from database_handle.database import get_db
from database_handle.models.audios import Audio, StatusEnum
from database_handle.models.bindings import (
    Binding,
    BindingEntry,
    BindingModel,
)
from database_handle.models.categories import Category
from database_handle.models.texts import Text
from database_handle.utils.pagination import with_paginated

BindingAlias = aliased(Binding, name="binding")
CategoryAlias = aliased(Category, name="category")
AudioAlias = aliased(Audio, name="audio")
TextAlias = aliased(Text, name="text")


@dataclass
class BindingsQueries:
    session: AsyncSession

    async def get_all(
        self,
        category_name: str | None = None,
        category_id: str | None = None,
        include_none: bool = False,
        skip_empty: bool = False,
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
        if category_id:
            stmt = stmt.where(CategoryAlias.id == category_id)
        if include_none and category_id is None:
            stmt = stmt.where(CategoryAlias.id.is_(None))
        if skip_empty:
            stmt = stmt.where(func.trim(TextAlias.text) != "")

        result = (await self.session.execute(stmt)).all()

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

    async def get_paginated(self, page: int = 0, limit: int = 20):
        stmt = (
            select(BindingAlias, CategoryAlias, AudioAlias, TextAlias)
            .outerjoin(CategoryAlias)
            .join(AudioAlias)
            .join(TextAlias)
            .where(AudioAlias.audio_status != StatusEnum.waiting)
            .order_by(AudioAlias.file_name)
        )

        def transform_row(row):
            return BindingModel(
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

        return await with_paginated(self.session, stmt, page, limit, transform_row)

    async def create(self, binding: Binding):
        self.session.add(binding)

    async def remove(self, id: UUID4):
        stmt = delete(Binding).where(Binding.id == id)
        await self.session.execute(stmt)

    async def update_category(
        self, binding_id: UUID4, category_id: UUID4 | None
    ):
        stmt = (
            update(Binding)
            .where(Binding.id == binding_id)
            .values(category_id=category_id)
        )
        await self.session.execute(stmt)


def get_bindings_queries(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BindingsQueries:
    return BindingsQueries(session=db)
