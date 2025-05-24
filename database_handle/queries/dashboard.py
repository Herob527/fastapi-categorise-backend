from sqlalchemy import  func

from database_handle.models.audios import Audio
from database_handle.models.bindings import Binding
from database_handle.models.categories import Category
from database_handle.models.texts import Text

from sqlalchemy.orm import Session

def get_categories_count(session: Session) -> int:
    return session.query(func.count(Category.id)).scalar()

def get_total_bindings_count(session: Session) -> int:
    return session.query(func.count(Binding.id)).scalar()

def get_category_with_most_bindings(session: Session) -> tuple[str, int]:
    subquery = (
        session.query(
            Category.name,
            func.count(Binding.id).label("bindings_count")
        )
        .join(Binding, Binding.category_id == Category.id)
        .group_by(Category.id)
        .subquery()
    )

    result = session.query(subquery.c.name, subquery.c.bindings_count).order_by(subquery.c.bindings_count.desc()).first()

    if result is None:
        return ("", 0)
    
    return (str(result[0]), int(result[1]))

def get_uncategorized_count(session: Session) -> int:
    return session.query(func.count(Binding.id)).filter(Binding.category_id.is_(None)).scalar()

def get_categorized_count(session: Session) -> int:
    return session.query(func.count(Binding.id)).filter(Binding.category_id.is_not(None)).scalar()

def get_total_audio_duration(session: Session) -> float:
    return session.query(func.sum(Audio.audio_length)).scalar() or 0.0

def get_filled_transcript_count(session: Session) -> int:
    return (
        session.query(func.count(Text.id))
        .join(Binding, Binding.text_id == Text.id)
        .filter(func.trim(Text.text) != "")
        .scalar()
    )

def get_empty_transcript_count(session: Session) -> int:
    return (
        session.query(func.count(Text.id))
        .join(Binding, Binding.text_id == Text.id)
        .filter(func.trim(Text.text) == "")
        .scalar()
    )
