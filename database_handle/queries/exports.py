from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi import Depends
from database_handle.database import get_db


class ExportsQueries:
    db: AsyncSession

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def exists(self, id: str):
        pass

    async def insert(self, id: str):
        pass

    async def remove(self, id: str):
        pass
