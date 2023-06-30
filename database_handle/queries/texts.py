from sqlalchemy.orm import Session
from database_handle.models.texts import Texts


def get_one_text(db: Session, id: str):
    return db.query(Texts).filter(Texts.id == id).first()


def get_all_texts(db: Session):
    return db.query(Texts).all()


def update_text(db: Session, text: Texts):
    db.query(Texts).filter(Texts.id == text.id).update(text.dict())
    db.commit()
    db.refresh(text)


def remove_text(db: Session, id: str):
    db.query(Texts).filter(Texts.id == id).delete()
    db.commit()


def create_text(db: Session, text: Texts):
    db.add(text)
