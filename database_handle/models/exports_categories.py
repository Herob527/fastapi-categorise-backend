from sqlalchemy import Column, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from ..database import Base


class ExportsCategories(Base):
    __tablename__ = "exports_categories"

    id = Column(Uuid, primary_key=True, index=True)
    export_id = Column(
        Uuid, ForeignKey("exports.id", ondelete="CASCADE"), nullable=False
    )
    category_id = Column(Uuid, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category")
