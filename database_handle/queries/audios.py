from sqlalchemy.orm import Session

from database_handle.models.audios import Audios


def audio_exists(db: Session, audio: Audios):
    return (
        db.query(Audios)
        .filter(
            Audios.file_name == audio.file_name,
            Audios.audio_length == audio.audio_length,
            Audios.frequency == audio.frequency,
            Audios.channels == audio.channels,
        )
        .first()
        is not None
    )


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
