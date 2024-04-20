from sqlalchemy import Column, ForeignKey, Uuid
from sqlalchemy.orm import relationship

from database_handle.models.audios import AudioModel
from database_handle.models.categories import CategoryModel
from database_handle.models.texts import TextModel
from ..database import Base
from pydantic import BaseModel


class Binding(Base):
    __tablename__ = "bindings"

    id = Column(Uuid, primary_key=True, index=True)
    category_id = Column(
        Uuid,
        ForeignKey("categories.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    audio_id = Column(
        Uuid,
        ForeignKey("audios.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    text_id = Column(
        Uuid,
        ForeignKey("texts.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    category = relationship("Categories")
    audio = relationship("Audios")
    text = relationship("Texts")


class BindingModel(BaseModel):
    id: str
    category_id: str
    audio_id: str
    text_id: str
    category: CategoryModel
    audio: AudioModel
    text: TextModel

    class Config:
        orm_mode = True
