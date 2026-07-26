from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from database_handle.database import get_db
from database_handle.queries.texts import TextsQueries

__all__ = ["router"]

router = APIRouter(
    tags=["Texts"],
    prefix="/texts",
    responses={404: {"description": "Not found"}},
)


@router.patch("/{text_id}")
async def update_text(
    text_id: UUID4,
    new_text: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    async with db.begin() as session:
        queries = TextsQueries(session=session.session)
        text = await queries.get_by_id(text_id)
        if text is None:
            return
        text.text = new_text
        await queries.update(text)
