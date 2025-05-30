import asyncio
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
    # Create a list of all async operations
    tasks = [
        get_categories_count(db),
        get_total_bindings_count(db),
        get_category_with_most_bindings(db),
        get_uncategorized_count(db),
        get_categorized_count(db),
        get_total_audio_duration(db),
        get_filled_transcript_count(db),
        get_empty_transcript_count(db),
    ]

    # Execute all queries concurrently
    results = await asyncio.gather(*tasks)

    # Unpack results in order
    (
        categories_count,
        total_bindings_count,
        category_with_most_bindings,
        uncategorized_count,
        categorized_count,
        total_audio_duration,
        filled_transcript_count,
        empty_transcript_count,
    ) = results

    return DashboardModel(
        categories_count=categories_count,
        total_bindings_count=total_bindings_count,
        category_with_most_bindings=category_with_most_bindings,
        uncategorizaed_count=uncategorized_count,
        categorized_count=categorized_count,
        total_audio_duration=round(total_audio_duration, 2),
        filled_transcript_count=filled_transcript_count,
        empty_transcript_count=empty_transcript_count,
    )
