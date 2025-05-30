from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from database_handle.database import get_db
from database_handle.models.texts import Text
from database_handle.queries.texts import (
    update_text as text_update,
)

__all__ = ["router"]

router = APIRouter(
    tags=["Texts"],
    prefix="/texts",
    responses={404: {"description": "Not found"}},
)


@router.patch("/{text_id}")
async def update_text(
    text_id: UUID4, new_text: str, db: AsyncSession = Depends(get_db)
) -> None:
    await text_update(db, Text(id=text_id, text=new_text))
    await db.commit()
    return None
