from sqlalchemy.orm import Session

from database_handle.models.categories import Categories


def get_one_category(db: Session, id: str):
    return db.query(Categories).filter(Categories.id == id).first()


def get_all_categories(db: Session):
    return db.query(Categories).all()


def remove_category(db: Session, id: str):
    db.query(Categories).filter(Categories.id == id).delete(synchronize_session=False)
    db.commit()


def create_category(db: Session, category: Categories):
    db.add(category)


def update_category(db: Session, category: Categories):
    db.query(Categories).filter(Categories.id == category.id).update(
        category.dict(), synchronize_session=False
    )
    db.commit()
