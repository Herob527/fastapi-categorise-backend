from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from minio import select
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import update

from database_handle.database import get_db
from database_handle.models.audios import Audio, StatusEnum


@dataclass
class AudioQueries:
    session: AsyncSession

    async def update_audio(
        self,
        audio_id: UUID4,
        status: StatusEnum,
        audio_length: float | None = None,
        url: str | None = None,
    ):
        args: dict[str, str | float | StatusEnum] = {"audio_status": status}
        if audio_length is not None:
            args["audio_length"] = audio_length
        if url is not None:
            args["url"] = url
        await self.session.execute(
            update(Audio).where(Audio.id == audio_id).values(**args)
        )

    async def exists(self, name: str):
        stmt = select(Audio).filter_by(file_name=name).limit(1)
        result = await self.session.scalar(stmt)
        return result is not None


def get_audio_queries(db: Annotated[AsyncSession, Depends(get_db)]) -> AudioQueries:
    return AudioQueries(session=db)
