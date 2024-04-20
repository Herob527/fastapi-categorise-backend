from pydantic import BaseModel
from sqlalchemy import Column, String, Uuid
from ..database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Uuid, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)


class CategoryModel(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True
