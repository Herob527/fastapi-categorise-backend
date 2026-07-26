from fastapi import APIRouter, Depends

from database_handle.models.dashboard import DashboardModel
from database_handle.queries.dashboard import DashboardQueries, get_dashboard_queries

__all__ = ["router"]

router = APIRouter(
    tags=["Dashboard"],
    prefix="/dashboard",
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=DashboardModel)
async def get_dashboard(queries: DashboardQueries = Depends(get_dashboard_queries)):
    categories_count = await queries.get_categories_count()
    total_bindings_count = await queries.get_total_bindings_count()
    category_with_most_bindings = await queries.get_category_with_most_bindings()
    uncategorized_count = await queries.get_uncategorized_count()
    categorized_count = await queries.get_categorized_count()
    total_audio_duration = await queries.get_total_audio_duration()
    filled_transcript_count = await queries.get_filled_transcript_count()
    empty_transcript_count = await queries.get_empty_transcript_count()

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
