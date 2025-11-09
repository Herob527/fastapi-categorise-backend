import enum
from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy import Column, Float, String, Uuid, Enum

from ..database import Base


class StatusEnum(enum.Enum):
    waiting = 0
    available = 1


class Audio(Base):
    __tablename__ = "audios"

    id = Column(Uuid, primary_key=True, index=True)
    url = Column(String, nullable=True, unique=True)
    file_name = Column(String, nullable=False)
    audio_length = Column(Float, nullable=True)
    audio_status = Column(Enum(StatusEnum), default=StatusEnum.waiting)


class AudioModel(BaseModel):
    id: UUID4
    url: str
    file_name: str
    audio_length: float | None
    audio_status: StatusEnum

    class Config:
        from_attributes = True
