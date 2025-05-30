from sqlalchemy import select, func
from sqlalchemy.ext.asyncio.session import AsyncSession

from database_handle.models.audios import Audio
from database_handle.models.bindings import Binding
from database_handle.models.categories import Category
from database_handle.models.texts import Text


async def get_categories_count(session: AsyncSession):
    result = await session.scalar(select(func.count(Category.id)))
    return result


async def get_total_bindings_count(session: AsyncSession):
    result = await session.scalar(select(func.count(Binding.id)))
    return result


async def get_category_with_most_bindings(session: AsyncSession):
    subquery = (
        select(Category.name, func.count(Binding.id).label("bindings_count"))
        .select_from(Category)
        .join(Binding, Binding.category_id == Category.id)
        .group_by(Category.id)
        .subquery()
    )

    result = (
        await session.execute(
            select(subquery.c.name, subquery.c.bindings_count)
            .order_by(subquery.c.bindings_count.desc())
            .limit(1)
        )
    ).first()

    return (str(result[0]) if result else "", 0)


async def get_uncategorized_count(session: AsyncSession):
    result = await session.scalar(
        select(func.count(Binding.id)).filter(Binding.category_id.is_(None))
    )
    return result


async def get_categorized_count(session: AsyncSession):
    result = await session.scalar(
        select(func.count(Binding.id)).filter(Binding.category_id.is_not(None))
    )
    return result


async def get_total_audio_duration(session: AsyncSession):
    result = await session.scalar(select(func.sum(Audio.audio_length)))
    return float(result or 0.0)


async def get_filled_transcript_count(session: AsyncSession):
    result = await session.scalar(
        select(func.count(Text.id))
        .select_from(Text)
        .join(Binding, Binding.text_id == Text.id)
        .filter(func.trim(Text.text) != "")
    )
    return result


async def get_empty_transcript_count(session: AsyncSession):
    result = await session.scalar(
        select(func.count(Text.id))
        .select_from(Text)
        .join(Binding, Binding.text_id == Text.id)
        .filter(func.trim(Text.text) == "")
    )
    return result
