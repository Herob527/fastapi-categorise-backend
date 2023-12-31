from sqlalchemy import Column, Float, Integer, String, Uuid
from ..database import Base


class Audios(Base):
    __tablename__ = "audios"

    id = Column(Uuid, primary_key=True, index=True)
    url = Column(String, nullable=False, unique=True)
    file_name = Column(String, nullable=False)
    channels = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)
    audio_length = Column(Float, nullable=False)
