from sqlalchemy.orm import Session
from database_handle.models.texts import Text


def get_one_text(db: Session, id: str):
    return db.query(Text).filter(Text.id == id).first()


def get_all_texts(db: Session):
    return db.query(Text).all()


def update_text(db: Session, text: Text):
    db.query(Text).filter(Text.id == text.id).update(text.dict())
    db.commit()
    db.refresh(text)


def remove_text(db: Session, id: str):
    db.query(Text).filter(Text.id == id).delete()
    db.commit()


def create_text(db: Session, text: Text):
    db.add(text)
