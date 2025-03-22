from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import UUID4
from sqlalchemy.orm import Session

from database_handle.database import get_db
from database_handle.models.categories import Category, CategoryModel
from database_handle.queries.categories import (
    create_category,
    get_one_category,
)
from database_handle.queries.categories import (
    get_all_categories as all_categories_query,
)
from database_handle.queries.categories import (
    remove_category as category_delete,
)
from database_handle.queries.categories import (
    update_category as category_update,
)

__all__ = ["router"]

router = APIRouter(
    tags=["Category"],
    prefix="/categories",
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=List[CategoryModel])
async def get_all_categories(db: Session = Depends(get_db)):
    return all_categories_query(db)


@router.post("")
async def post_new_category(
    id: UUID4 | None = None, category: str = Form(), db: Session = Depends(get_db)
) -> None:
    if id is not None:
        res = get_one_category(db=db, id=id)
        if res is not None:
            db.rollback()
            raise HTTPException(
                status_code=400, detail=f"Category '{category}' already exists"
            )
    new_category = Category(id=id or uuid4(), name=category)
    try:
        create_category(db=db, category=new_category)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Server error - something with session"
        )
    return None


@router.patch("/{id}")
async def update_category(
    id: UUID4, new_category_name: str = Form(), db: Session = Depends(get_db)
):
    category = get_one_category(db, id)
    if category is None:
        return {"res": "Not found"}
    new_category = Category(id=category.id, name=new_category_name)
    category_update(db, new_category)


@router.delete("/{category_name}")
async def remove_category(category_name: str, db: Session = Depends(get_db)):
    res = category_delete(db=db, name=category_name)
    return res
