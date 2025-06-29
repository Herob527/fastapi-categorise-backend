from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy import Column, Float, String, Uuid

from ..database import Base


class Audio(Base):
    __tablename__ = "audios"

    id = Column(Uuid, primary_key=True, index=True)
    url = Column(String, nullable=False, unique=True)
    file_name = Column(String, nullable=False)
    audio_length = Column(Float, nullable=False)


class AudioModel(BaseModel):
    id: UUID4
    url: str
    file_name: str
    audio_length: float

    class Config:
        from_attributes = True
