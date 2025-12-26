from typing import Annotated, List
from uuid import uuid4

from pydantic import BaseModel

from database_handle.models.texts import Text
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic.types import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from database_handle.database import get_db
from database_handle.models.audios import Audio, StatusEnum
from database_handle.models.bindings import Binding, BindingModel, PaginatedBindingModel
from database_handle.models.categories import Category
from database_handle.queries.bindings import (
    create_binding as create_new_binding,
)
from database_handle.queries.bindings import (
    get_all_bindings as all_bindings_query,
)
from database_handle.queries.bindings import (
    get_total_bindings,
    update_binding_category,
)
from database_handle.queries.bindings import (
    get_paginated_bindings as paginated_bindings_query,
)
from database_handle.queries.bindings import (
    remove_binding as binding_remove,
)
from database_handle.queries.categories import (
    create_category,
    get_one_category_by_name,
)
from routes.audios import delete_audio, upload_audio
from services import minio_service

__all__ = ["router"]

router = APIRouter(
    tags=["Bindings"],
    prefix="/bindings",
    responses={404: {"description": "Not found"}},
)


@router.get("/count")
async def get_count(db: AsyncSession = Depends(get_db)):
    return (await get_total_bindings(db)) or 0


@router.get("", response_model=PaginatedBindingModel)
async def get_paginated_bindings(
    page: int = 0, per_page: int = 10, db: AsyncSession = Depends(get_db)
):
    if page < 0:
        raise HTTPException(
            status_code=400, detail="Page must be greater than or equal 0"
        )
    if per_page <= 0:
        raise HTTPException(status_code=400, detail="Page size must be greater than 0")

    bindings, pagination = await paginated_bindings_query(
        page=page, limit=per_page, db=db
    )

    return PaginatedBindingModel(
        bindings=bindings,
        page=page,
        pagination=pagination,
    )


@router.get("/all", response_model=List[BindingModel])
async def get_all_bindings(
    db: AsyncSession = Depends(get_db), category: str | None = None
):
    return await all_bindings_query(db, category)


class CreateResponseModel(BaseModel):
    binding_id: UUID4


@router.post("", response_model=CreateResponseModel)
async def create_binding(
    audio: Annotated[UploadFile, File()],
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    binding_id = uuid4()
    category_exist = (
        await get_one_category_by_name(db=db, name=category)
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
            await create_category(db=db, category=new_category)
        new_text = Text(id=binding_id, text="")
        db.add(new_text)
        db.add(
            Audio(
                id=binding_id, file_name=audio.filename, audio_status=StatusEnum.waiting
            )
        )
        await create_new_binding(db=db, binding=new_binding)
        await db.commit()
    except HTTPException as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return CreateResponseModel(binding_id=binding_id)


@router.delete("/{binding_id}")
async def remove_binding(
    binding_id: UUID4,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    await binding_remove(db, binding_id)
    await db.commit()

    async def delete():
        # Create a new session for the background task
        from database_handle.database import get_sessionmanager

        async with get_sessionmanager().session() as bg_session:
            await delete_audio(binding_id, bg_session)
            await bg_session.commit()

    background_tasks.add_task(delete)
    return {"hejo": binding_id}


@router.put("/{binding_id}/category_assign/{category_id}")
async def binding_category_update(
    binding_id: UUID4, category_id: UUID4, db: AsyncSession = Depends(get_db)
):
    await update_binding_category(binding_id, category_id, db)
    await db.commit()


@router.put("/{binding_id}/remove_category")
async def binding_category_remove(
    binding_id: UUID4, db: AsyncSession = Depends(get_db)
):
    await update_binding_category(binding_id, None, db)
    await db.commit()
