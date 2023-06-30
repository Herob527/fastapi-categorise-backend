from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import UUID4
from sqlalchemy.orm import Session

from database_handle.database import get_db
from database_handle.models.categories import Categories
from database_handle.queries.categories import create_category

__all__ = ["router"]

router = APIRouter(
    tags=["Category"],
    prefix="/categories",
    responses={404: {"description": "Not found"}},
)


@router.get("/{category_id}")
async def get_category(category_id: int):
    print(f"Got category with ID: {category_id}")
    return {"test": category_id}


@router.get("/")
async def get_all_categories():
    print("Got all categories")
    return {"test": "test"}


@router.post("/")
async def post_new_category(
    id: UUID4 = Form(), category: str = Form(), db: Session = Depends(get_db)
):
    new_category = Categories(id=id, name=category)
    try:
        create_category(db=db, category=new_category)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Category {category} already exists"
        )
    return {"test": "test"}


@router.patch("/{category_id}")
async def update_category(category_id: int):
    print(f"Updated category with name: {category_id}")
    return {"test": category_id}


@router.delete("/{category_id}")
async def remove_category(category_id: int):
    print(f"Removed category with ID: {category_id}")
    return {"test": category_id}
