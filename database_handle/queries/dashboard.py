from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from database_handle.database import get_db
from database_handle.models.audios import Audio
from database_handle.models.bindings import Binding
from database_handle.models.categories import Category, Visibility
from database_handle.models.texts import Text


@dataclass
class DashboardQueries:
    session: AsyncSession

    async def get_categories_count(self):
        result = await self.session.scalar(
            select(func.count(Category.id)).where(
                Category.visibility == Visibility.PUBLIC
            )
        )
        return result

    async def get_total_bindings_count(self):
        result = await self.session.scalar(select(func.count(Binding.id)))
        return result

    # TODO: Switch from tuple into some dict
    async def get_category_with_most_bindings(self):
        subquery = (
            select(Category.name, func.count(Binding.id).label("bindings_count"))
            .select_from(Category)
            .join(Binding, Binding.category_id == Category.id)
            .group_by(Category.id, Category.name)
            .order_by(func.count(Binding.id).desc())
            .where(Category.visibility == Visibility.PUBLIC)
            .limit(1)
        )

        result = (await self.session.execute(subquery)).first()
        if not result:
            return "", 0

        return (result[0], result[1])

    async def get_uncategorized_count(self):
        result = await self.session.scalar(
            select(func.count(Binding.id)).filter(Binding.category_id.is_(None))
        )
        return result

    async def get_categorized_count(self):
        result = await self.session.scalar(
            select(func.count(Binding.id)).filter(Binding.category_id.is_not(None))
        )
        return result

    async def get_total_audio_duration(self):
        result = await self.session.scalar(select(func.sum(Audio.audio_length)))
        return float(result or 0.0)

    async def get_filled_transcript_count(self):
        result = await self.session.scalar(
            select(func.count(Text.id))
            .select_from(Text)
            .join(Binding, Binding.text_id == Text.id)
            .filter(func.trim(Text.text) != "")
        )
        return result

    async def get_empty_transcript_count(self):
        result = await self.session.scalar(
            select(func.count(Text.id))
            .select_from(Text)
            .join(Binding, Binding.text_id == Text.id)
            .filter(func.trim(Text.text) == "")
        )
        return result


def get_dashboard_queries(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardQueries:
    return DashboardQueries(session=db)
