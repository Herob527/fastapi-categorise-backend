import enum
from pydantic import BaseModel, NaiveDatetime
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
    archive_url = Column(String, nullable=True, default=None)


class ExportModel(BaseModel):
    status: ExportStatus
    created_at: NaiveDatetime
    updated_at: NaiveDatetime
    archive_url: str | None
