import enum
from sqlalchemy import Column, DateTime, String, Enum, Uuid

from ..database import Base
from sqlalchemy.sql import func


class ExportStatus(enum.Enum):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3


class Exports(Base):
    __tablename__ = "exports"

    id = Column(Uuid, primary_key=True, index=True)
    status = Column(Enum(ExportStatus), default=ExportStatus.PENDING)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now())
