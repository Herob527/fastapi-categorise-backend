from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy import Column, String, Uuid

from ..database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Uuid, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)


class CategoryModel(BaseModel):
    id: UUID4
    name: str

    class Config:
        orm_mode = True
