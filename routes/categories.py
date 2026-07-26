from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import UUID4

from database_handle.models.categories import Category, CategoryModel
from database_handle.queries.categories import CategoriesQueries, get_categories_queries

__all__ = ["router"]

router = APIRouter(
    tags=["Category"],
    prefix="/categories",
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=list[CategoryModel])
async def get_all_categories(
    queries: CategoriesQueries = Depends(get_categories_queries),
):
    data = await queries.get_all()
    print(data)
    return data


@router.post("/")
async def post_new_category(
    id: UUID4 | None = None,
    category: str = Form(),
    queries: CategoriesQueries = Depends(get_categories_queries),
) -> None:
    if id is not None:
        res = await queries.get_one(id=id)
        if res is not None:
            raise HTTPException(
                status_code=400, detail=f"Category '{category}' already exists"
            )

    res = await queries.get_one_by_name(name=category)
    if res is not None:
        raise HTTPException(
            status_code=400, detail=f"Category '{category}' already exists"
        )

    new_category = Category(id=id or uuid4(), name=category)
    try:
        await queries.create(category=new_category)
        # commit handled by session from dependency
    except Exception:
        raise HTTPException(
            status_code=500, detail="Server error - something with session"
        )


@router.patch("/{id}")
async def update_category(
    id: UUID4,
    new_category_name: str = Form(),
    queries: CategoriesQueries = Depends(get_categories_queries),
):
    category = await queries.get_one(id)
    if category is None:
        return {"res": "Not found"}
    new_category = Category(id=category.id, name=new_category_name)
    await queries.update(new_category)


@router.delete("/{category_name}")
async def remove_category(
    category_name: str,
    queries: CategoriesQueries = Depends(get_categories_queries),
):
    await queries.remove(name=category_name)
