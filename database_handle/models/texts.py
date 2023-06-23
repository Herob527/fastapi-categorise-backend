from sqlalchemy import Column, Integer, String
from ..database import Base


class Texts(Base):
    __tablename__ = "texts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
