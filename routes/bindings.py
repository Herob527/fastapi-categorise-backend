from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from typing import Annotated
from sqlalchemy.orm import Session
from uuid import uuid4
from database_handle.database import get_db
from database_handle.models.audios import Audios
from database_handle.models.bindings import Bindings
from database_handle.models.categories import Categories
from database_handle.queries.bindings import (
    get_one_binding,
    create_binding as create_new_binding,
    get_total_bindings,
    get_paginated_bindings as paginated_bindings_query,
    get_all_bindings as all_bindings_query,
)
import asyncio
from database_handle.queries.categories import (
    create_category,
    get_categories_count,
    get_one_category,
)
from routes.audios import post_new_audio
from routes.categories import post_new_category
from routes.texts import post_new_text

__all__ = ["router"]

router = APIRouter(
    tags=["Bindings"],
    prefix="/bindings",
    responses={404: {"description": "Not found"}},
)


@router.get("/count")
def get_count(db: Session = Depends(get_db)):
    return get_total_bindings(db) or 0


@router.get("")
def get_paginated_bindings(
    page: int = 1, per_page: int = 10, db: Session = Depends(get_db)
):
    return paginated_bindings_query(page=page, limit=per_page, db=db)


@router.get("/all")
def get_all_bindings(db: Session = Depends(get_db)):
    query_data = all_bindings_query(db)
    return query_data


@router.get("/{binding_id}")
def get_binding(binding_id: str, db: Session = Depends(get_db)):
    return get_one_binding(db, binding_id)


@router.post("")
async def create_binding(
    audio: Annotated[UploadFile, File()],
    category: str = Form(default="unknown"),
    db: Session = Depends(get_db),
):
    binding_id = uuid4()
    category_exist = get_one_category(db=db, name=category)
    category_id = binding_id if category_exist is None else category_exist.id
    new_binding = Bindings(
        id=binding_id, category_id=category_id, audio_id=binding_id, text_id=binding_id
    )
    new_category = Categories(id=id, name=category)
    try:
        await asyncio.gather(
            *[
                post_new_audio(id=binding_id, file=audio, db=db),
                post_new_text(id=binding_id, text="", db=db),
            ]
        )

        create_new_binding(db=db, binding=new_binding)
        create_category(db=db, category=new_category)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    return {"Test": category}


@router.delete("/{binding_id}")
def remove_binding(binding_id: int):
    print(f"Removed binding with id {binding_id}")
    return {"hejo": binding_id}
