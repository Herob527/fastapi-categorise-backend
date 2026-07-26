from sqlalchemy.ext.asyncio import AsyncSessionTransaction
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.sql.expression import select, update

from database_handle.database import get_db
from database_handle.models.texts import Text


@dataclass
class TextsQueries:
    session: AsyncSession

    async def get_by_id(self, id: UUID4):
        return await self.session.scalar(select(Text).where(Text.id == id))

    async def update(self, text: Text):
        stmt = update(Text).where(Text.id == text.id).values(text=text.text)
        await self.session.execute(stmt)

    async def create(self, text: Text):
        self.session.add(text)


def get_texts_queries(db: Annotated[AsyncSession, Depends(get_db)]) -> TextsQueries:
    return TextsQueries(session=db)
