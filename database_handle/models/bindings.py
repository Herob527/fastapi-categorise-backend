from typing import List
from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy import Column, ForeignKey, Uuid
from sqlalchemy.orm import relationship

from database_handle.models.audios import AudioModel
from database_handle.models.categories import CategoryModel
from database_handle.models.texts import TextModel

from ..database import Base


class Binding(Base):
    __tablename__ = "bindings"

    id = Column(Uuid, primary_key=True, index=True)
    category_id = Column(
        Uuid,
        ForeignKey("categories.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
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
    category = relationship("Category")
    audio = relationship("Audio")
    text = relationship("Text")


class PaginationModel(BaseModel):
    total: int


class BindingEntry(BaseModel):
    id: UUID4
    category_id: UUID4 | None
    audio_id: UUID4
    text_id: UUID4

    class Config:
        from_attributes = True


class BindingModel(BaseModel):
    binding: BindingEntry
    category: CategoryModel | None
    audio: AudioModel
    text: TextModel

    class Config:
        from_attributes = True


class PaginatedBindingModel(BaseModel):
    bindings: List[BindingModel]
    pagination: PaginationModel
    page: int
