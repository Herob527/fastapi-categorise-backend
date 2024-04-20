from pydantic import UUID4
from sqlalchemy.orm import Session

from database_handle.models.audios import Audio


def audio_exists(db: Session, audio: Audio):
    return (
        db.query(Audio)
        .filter(
            Audio.file_name == audio.file_name,
            Audio.audio_length == audio.audio_length,
            Audio.frequency == audio.frequency,
            Audio.channels == audio.channels,
        )
        .first()
        is not None
    )


def get_one_audio(db: Session, id: UUID4):
    return db.query(Audio).filter(Audio.id == id).limit(1).first()


def get_all_audios(db: Session):
    return db.query(Audio).all()


def create_audio(db: Session, audio: Audio):
    db.add(audio)


def remove_audio(db: Session, id: str):
    db.query(Audio).filter(Audio.id == id).delete()
    db.commit()


def update_audio(db: Session, id: str, audio: Audio):
    db.query(Audio).filter(Audio.id == id).update(values=audio)
    db.commit()
