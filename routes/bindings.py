from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from database_handle.database import get_db
from database_handle.models.audios import Audio, StatusEnum
from database_handle.models.bindings import Binding, BindingModel, PaginatedBindingModel
from database_handle.models.categories import Category
from database_handle.models.texts import Text
from database_handle.queries.bindings import BindingsQueries, get_bindings_queries
from database_handle.queries.categories import CategoriesQueries, get_categories_queries
from routes.audios import delete_audio

__all__ = ["router"]

router = APIRouter(
    tags=["Bindings"],
    prefix="/bindings",
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=PaginatedBindingModel)
async def get_paginated_bindings(
    page: int = 0,
    per_page: int = 10,
    queries: BindingsQueries = Depends(get_bindings_queries),
):
    if page < 0:
        raise HTTPException(
            status_code=400, detail="Page must be greater than or equal 0"
        )
    if per_page <= 0:
        raise HTTPException(status_code=400, detail="Page size must be greater than 0")

    bindings, pagination = await queries.get_paginated(page=page, limit=per_page)

    return PaginatedBindingModel(
        items=bindings,
        pagination=pagination,
    )


@router.get("/all", response_model=list[BindingModel])
async def get_all_bindings(
    queries: BindingsQueries = Depends(get_bindings_queries),
    category: str | None = None,
):
    return await queries.get_all(category_name=category)


class CreateResponseModel(BaseModel):
    binding_id: UUID4


@router.post("", response_model=CreateResponseModel)
async def create_binding(
    audio: Annotated[UploadFile, File()],
    category: str | None = None,
    bindings_queries: BindingsQueries = Depends(get_bindings_queries),
    categories_queries: CategoriesQueries = Depends(get_categories_queries),
    db: AsyncSession = Depends(get_db),
):
    binding_id = uuid4()
    category_exist = (
        await categories_queries.get_one_by_name(name=category)
        if category is not None
        else None
    )
    if not audio.filename:
        raise HTTPException(
            status_code=400, detail="Audio file is required to have filename"
        )
    category_id = uuid4() if category_exist is None else category_exist.id
    new_binding = Binding(
        id=binding_id,
        category_id=category_id if category is not None else None,
        audio_id=binding_id,
        text_id=binding_id,
    )
    new_category = (
        Category(id=category_id, name=category) if category is not None else None
    )
    try:
        if new_category is not None:
            await categories_queries.create(category=new_category)
        new_text = Text(id=binding_id, text="")
        db.add(new_text)
        db.add(
            Audio(
                id=binding_id, file_name=audio.filename, audio_status=StatusEnum.waiting
            )
        )
        await bindings_queries.create(binding=new_binding)
        await db.commit()
    except HTTPException as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return CreateResponseModel(binding_id=binding_id)


@router.delete("/{binding_id}")
async def remove_binding(
    binding_id: UUID4,
    queries: BindingsQueries = Depends(get_bindings_queries),
    db: AsyncSession = Depends(get_db),
):
    await queries.remove(binding_id)

    await delete_audio(binding_id, db)
    await db.commit()

    return {"hejo": binding_id}


@router.put("/{binding_id}/category_assign/{category_id}")
async def binding_category_update(
    binding_id: UUID4,
    category_id: UUID4,
    queries: BindingsQueries = Depends(get_bindings_queries),
    db: AsyncSession = Depends(get_db),
):
    await queries.update_category(binding_id, category_id)
    await db.commit()


@router.put("/{binding_id}/remove_category")
async def binding_category_remove(
    binding_id: UUID4,
    queries: BindingsQueries = Depends(get_bindings_queries),
    db: AsyncSession = Depends(get_db),
):
    await queries.update_category(binding_id, None)
    await db.commit()
