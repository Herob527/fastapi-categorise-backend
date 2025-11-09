from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession

from database_handle.database import get_db
from database_handle.models.dashboard import DashboardModel
from database_handle.queries.dashboard import (
    get_categories_count,
    get_categorized_count,
    get_category_with_most_bindings,
    get_empty_transcript_count,
    get_filled_transcript_count,
    get_total_audio_duration,
    get_total_bindings_count,
    get_uncategorized_count,
)


__all__ = ["router"]

router = APIRouter(
    tags=["Dashboard"],
    prefix="/dashboard",
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=DashboardModel)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    # Execute queries sequentially (SQLAlchemy async sessions don't support concurrent operations)
    categories_count = await get_categories_count(db)
    total_bindings_count = await get_total_bindings_count(db)
    category_with_most_bindings = await get_category_with_most_bindings(db)
    uncategorized_count = await get_uncategorized_count(db)
    categorized_count = await get_categorized_count(db)
    total_audio_duration = await get_total_audio_duration(db)
    filled_transcript_count = await get_filled_transcript_count(db)
    empty_transcript_count = await get_empty_transcript_count(db)

    return DashboardModel(
        categories_count=categories_count or 0,
        total_bindings_count=total_bindings_count or 0,
        category_with_most_bindings=category_with_most_bindings,
        uncategorizaed_count=uncategorized_count or 0,
        categorized_count=categorized_count or 0,
        total_audio_duration=round(total_audio_duration, 2),
        filled_transcript_count=filled_transcript_count or 0,
        empty_transcript_count=empty_transcript_count or 0,
    )
