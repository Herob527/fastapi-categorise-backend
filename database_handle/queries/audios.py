from dataclasses import dataclass
from enum import Enum
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import update

from database_handle.models.audios import Audio, StatusEnum


@dataclass()
class AudioQueries:
    session: AsyncSession

    async def update_audio(
        self, audio_id: UUID4, audio_length: float, status: StatusEnum
    ):
        await self.session.execute(
            update(Audio)
            .where(Audio.id == audio_id)
            .values(audio_length=audio_length, audio_status=status)
        )
