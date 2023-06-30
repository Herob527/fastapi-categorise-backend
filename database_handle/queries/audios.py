from sqlalchemy.orm import Session

from database_handle.models.audios import Audios
from pprint import pprint


def get_one_audio(db: Session, id: str):
    return db.query(Audios).filter(Audios.id == id).first()


def get_all_audios(db: Session):
    return db.query(Audios).all()


def create_audio(db: Session, audio: Audios):
    db.add(audio)


def remove_audio(db: Session, id: str):
    db.query(Audios).filter(Audios.id == id).delete()
    db.commit()


def update_audio(db: Session, id: str, audio: Audios):
    db.query(Audios).filter(Audios.id == id).update(values=audio)
    db.commit()
