from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import UUID4
from sqlalchemy.orm import Session

from database_handle.database import get_db
from database_handle.models.categories import Categories
from database_handle.queries.categories import (
    create_category,
    get_all_categories as all_categories_query,
    get_one_category,
    remove_category as category_delete,
)

__all__ = ["router"]

router = APIRouter(
    tags=["Category"],
    prefix="/categories",
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def get_all_categories(db: Session = Depends(get_db)):
    return all_categories_query(db)


@router.post("")
async def post_new_category(
    id: UUID4 = Form(), category: str = Form(), db: Session = Depends(get_db)
):
    res = get_one_category(db=db, name=category)
    if res is not None:
        db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Category '{category}' already exists"
        )
    new_category = Categories(id=id, name=category)
    try:
        create_category(db=db, category=new_category)
    except Exception:
        pass
    db.commit()

    return {"test": "test"}


@router.patch("/{category_name}")
async def update_category(category_name: str, new_category_name: str = Form()):
    pass


@router.delete("/{category_name}")
async def remove_category(category_name: str, db: Session = Depends(get_db)):
    res = category_delete(db=db, name=category_name)
    return res
