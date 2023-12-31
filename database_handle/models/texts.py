from sqlalchemy import Column, String, Uuid
from ..database import Base


class Texts(Base):
    __tablename__ = "texts"

    id = Column(Uuid, primary_key=True, index=True)
    text = Column(String, nullable=False)
