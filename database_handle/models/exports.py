import enum
from sqlalchemy import Column, Float, String, Enum
from ..database import Base


class ExportStatus(enum.Enum):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3


class Exports(Base):
    __tablename__ = "exports"

    id = Column(String, primary_key=True, index=True)
    status = Column(Enum(ExportStatus), default=ExportStatus.PENDING)
