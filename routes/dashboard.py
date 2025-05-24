"""
Create endpoint for dashboard

- Attach filled transcripts amount
- Attach total transcripts amount
- Attach uncategorized files
- Attach categorized files
- Attach categories amount
- Attach audio total length
- Attach categories grouped by amounts attached
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session

from database_handle.database import get_db
from database_handle.models.dashboard import DashboardModel
from database_handle.queries.dashboard import get_categories_count, get_categorized_count, get_category_with_most_bindings, get_empty_transcript_count, get_filled_transcript_count, get_total_audio_duration, get_total_bindings_count, get_uncategorized_count


__all__ = ["router"]

router = APIRouter(
    tags=["Dashboard"],
    prefix="/dashboard",
    responses={404: {"description": "Not found"}},
)
@router.get("/", response_model=DashboardModel)
async def get_dashboard(db: Session = Depends(get_db)):
    categories_count = get_categories_count(db)
    total_bindings_count = get_total_bindings_count(db)
    category_with_most_bindings = get_category_with_most_bindings(db)
    uncategorized_count = get_uncategorized_count(db)
    categorized_count = get_categorized_count(db)
    total_audio_duration = round(get_total_audio_duration(db), 2)
    filled_transcript_count = get_filled_transcript_count(db)
    empty_transcript_count = get_empty_transcript_count(db)

    return DashboardModel(
        categories_count=categories_count,
        total_bindings_count=total_bindings_count,
        category_with_most_bindings=category_with_most_bindings,
        uncategorizaed_count=uncategorized_count,
        categorized_count=categorized_count,
        total_audio_duration=total_audio_duration,
        filled_transcript_count=filled_transcript_count,
        empty_transcript_count=empty_transcript_count
    )
