from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy import Column, String, Uuid

from ..database import Base


class Text(Base):
    __tablename__ = "texts"

    id = Column(Uuid, primary_key=True, index=True)
    text = Column(String, nullable=False)


class TextModel(BaseModel):
    id: UUID4
    text: str

    class Config:
        orm_mode = True
