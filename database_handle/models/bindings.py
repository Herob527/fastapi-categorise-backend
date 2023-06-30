from sqlalchemy import Column, ForeignKey, Integer, Uuid
from sqlalchemy.sql.sqltypes import UUID
from ..database import Base


class Bindings(Base):
    __tablename__ = "bindings"

    id = Column(Uuid, primary_key=True, index=True)
    category_id = Column(
        Uuid,
        ForeignKey("categories.id"),
        nullable=False,
    )
    audio_id = Column(Uuid, ForeignKey("audios.id"), nullable=False)
    text_id = Column(Uuid, ForeignKey("texts.id"), nullable=False)
