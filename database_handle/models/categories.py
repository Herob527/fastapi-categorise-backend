from sqlalchemy import Column, Integer, String, Uuid
from sqlalchemy.sql.sqltypes import UUID
from ..database import Base


class Categories(Base):
    __tablename__ = "categories"

    id = Column(Uuid, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
