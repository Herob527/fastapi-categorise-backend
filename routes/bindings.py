from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database_handle.database import get_db
from database_handle.models.audios import Audio, StatusEnum
from database_handle.models.bindings import Binding, BindingModel, PaginatedBindingModel
from database_handle.models.categories import Category
from database_handle.models.texts import Text
from database_handle.queries.bindings import BindingsQueries, get_bindings_queries
from database_handle.queries.categories import CategoriesQueries, get_categories_queries
from services.minio_service import minio_service

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
    if not audio.filename:
        raise HTTPException(
            status_code=400, detail="Audio file is required to have filename"
        )
    binding_id = uuid4()
    try:
        async with db.begin() as session:
            bindings_queries = BindingsQueries(session=session.session)
            categories_queries = CategoriesQueries(session=session.session)

            existing_category = (
                await categories_queries.get_by_name(name=category)
                if category is not None
                else None
            )
            category_id = uuid4() if existing_category is None else existing_category.id
            if existing_category is None and category is not None:
                await categories_queries.create(Category(id=category_id, name=category))
            await bindings_queries.create(
                Binding(
                    id=binding_id,
                    category_id=category_id if category is not None else None,
                    audio_id=binding_id,
                    text_id=binding_id,
                )
            )
            session.add(Text(id=binding_id, text=""))
            session.add(
                Audio(
                    id=binding_id,
                    file_name=audio.filename,
                    audio_status=StatusEnum.waiting,
                )
            )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
    return CreateResponseModel(binding_id=binding_id)


@router.delete("/{binding_id}")
async def remove_binding(
    binding_id: UUID4,
    db: AsyncSession = Depends(get_db),
):
    async with db.begin() as t:
        audio_record = await db.scalar(
            select(Audio).where(Audio.id == binding_id).limit(1)
        )
        if not audio_record:
            raise HTTPException(status_code=404, detail="Audio file not found")

        object_name = str(audio_record.url).split(f"{minio_service.bucket_name}/")[-1]
        success = await minio_service.delete_file(object_name)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete audio file")

        queries = BindingsQueries(session=t.session)
        await queries.remove(binding_id)
        await t.session.delete(audio_record)

    return {"hejo": binding_id}


@router.put("/{binding_id}/category_assign/{category_id}")
async def binding_category_update(
    binding_id: UUID4,
    category_id: UUID4,
    db: AsyncSession = Depends(get_db),
):
    async with db.begin() as session:
        queries = BindingsQueries(session=session.session)
        await queries.update_category(binding_id, category_id)


@router.put("/{binding_id}/remove_category")
async def binding_category_remove(
    binding_id: UUID4,
    db: AsyncSession = Depends(get_db),
):
    async with db.begin() as session:
        queries = BindingsQueries(session=session.session)
        await queries.update_category(binding_id, None)
