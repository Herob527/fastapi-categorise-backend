from sqlalchemy import Column, ForeignKey, Integer
from ..database import Base


class Bindings(Base):
    __tablename__ = "bindings"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
    )
    audio_id = Column(Integer, ForeignKey("audios.id"), nullable=False)
    text_id = Column(Integer, ForeignKey("texts.id"), nullable=False)
