from sqlalchemy.orm import Session
from database_handle.models.audios import Audios

from database_handle.models.bindings import Bindings
from database_handle.models.categories import Categories
from database_handle.models.texts import Texts


def get_one_binding(db: Session, id: str):
    return db.query(Bindings).filter(Bindings.id == id).first()


def get_all_bindings(db: Session):
    query = (
        db.query(Bindings, Categories, Audios, Texts)
        .join(Categories)
        .join(Audios)
        .join(Texts)
    )
    return query.all()


def get_paginated_bindings(db: Session, page: int = 0, limit: int = 20):
    return db.query(Bindings).limit(limit).offset(page * limit).all()


def get_total_bindings(db: Session):
    return db.query(Bindings).count()


def create_binding(db: Session, binding: Bindings):
    db.add(binding)


def remove_binding(db: Session, id: str):
    db.query(Bindings).filter(Bindings.id == id).delete()
    db.commit()
