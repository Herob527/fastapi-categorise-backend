from sqlalchemy import Column, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from ..database import Base


class Bindings(Base):
    __tablename__ = "bindings"

    id = Column(Uuid, primary_key=True, index=True)
    category_id = Column(
        Uuid,
        ForeignKey("categories.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    audio_id = Column(
        Uuid,
        ForeignKey("audios.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    text_id = Column(
        Uuid,
        ForeignKey("texts.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    category = relationship("Categories")
    audio = relationship("Audios")
    text = relationship("Texts")
