from sqlalchemy import Column, Float, Integer, String
from ..database import Base


class Audios(Base):
    __tablename__ = "audios"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=False, unique=True)
    channels = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)
    audio_length = Column(Float, nullable=False)
