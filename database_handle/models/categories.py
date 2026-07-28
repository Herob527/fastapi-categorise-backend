import enum

from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy import UUID, Column, Enum, String

from ..database import Base


class Visibility(enum.Enum):
    PUBLIC = 1
    HIDDEN = 0


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    visibility = Column(Enum(Visibility), default=Visibility.PUBLIC)


class CategoryModel(BaseModel):
    id: UUID4
    name: str

    class Config:
        from_attributes = True
