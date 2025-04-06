from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy import UUID, Column, String

from ..database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)


class CategoryModel(BaseModel):
    id: UUID4
    name: str

    class Config:
        from_attributes = True
