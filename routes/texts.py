from fastapi import APIRouter, Depends
from pydantic import UUID4

from database_handle.models.texts import Text
from database_handle.queries.texts import TextsQueries, get_texts_queries

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
    queries: TextsQueries = Depends(get_texts_queries),
) -> None:
    await queries.update(Text(id=text_id, text=new_text))
