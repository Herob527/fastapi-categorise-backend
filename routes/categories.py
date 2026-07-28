from database_handle.queries.bindings import BindingsQueries
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from database_handle.database import get_db
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
    queries: Annotated[CategoriesQueries, Depends(get_categories_queries)],
):
    return await queries.get_all()


@router.post("/")
async def post_new_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: UUID4 | None = None,
    category: str = Form(),
) -> None:
    async with db.begin() as session:
        queries = CategoriesQueries(session=session.session)
        res = await queries.get_by_id(id) if id else None
        if res is not None:
            raise HTTPException(
                status_code=400, detail=f"Category '{category}' already exists"
            )

        res = await queries.get_by_name(category)
        if res is not None:
            raise HTTPException(
                status_code=400, detail=f"Category '{category}' already exists"
            )

        await queries.create(Category(id=id or uuid4(), name=category))


@router.patch("/{id}")
async def update_category(
    id: UUID4,
    db: Annotated[AsyncSession, Depends(get_db)],
    new_category_name: str = Form(),
):
    async with db.begin() as session:
        queries = CategoriesQueries(session=session.session)
        category = await queries.get_by_id(id)
        if category is None:
            return {"res": "Not found"}
        category.name = new_category_name
        await queries.update(category)


@router.delete("/{category_name}")
async def remove_category(
    category_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    async with db.begin() as session:
        queries = CategoriesQueries(session=session.session)
        bindings_queries = BindingsQueries(session=session.session)

        entry = await queries.get_by_name(category_name)
        if entry is None:
            raise HTTPException(status_code=404, detail="Category not found")

        await queries.remove(category_name)
        await bindings_queries.remove_category(entry.id)
