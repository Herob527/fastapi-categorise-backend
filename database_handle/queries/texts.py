from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.sql.expression import update

from database_handle.models.texts import Text


async def update_text(db: AsyncSession, text: Text):
    stmt = update(Text).where(Text.id == text.id).values(text=text.text)
    await db.execute(stmt)


async def create_text(db: AsyncSession, text: Text):
    db.add(text)
