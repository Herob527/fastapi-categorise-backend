from dataclasses import dataclass
from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio.session import AsyncSession
from database_handle.database import get_db
from database_handle.models.exports import ExportStatus, Exports


@dataclass
class ExportsQueries:
    session: AsyncSession

    async def exists(self, id: str):
        stmt = select(Exports).filter_by(id=id).limit(1)
        result = await self.session.scalar(stmt)
        return result is not None

    async def schedule(self, id: str):
        self.session.add(Exports(id=id, status=ExportStatus.PENDING))

    async def set_status(self, id: str, status: ExportStatus):
        await self.session.execute(
            update(Exports).where(Exports.id == id).values(status=status)
        )

    async def remove(self, id: str):
        pass


def get_exports_queries(db: AsyncSession = Depends(get_db)) -> ExportsQueries:
    """Dependency function to inject ExportsQueries with database session."""
    return ExportsQueries(session=db)
