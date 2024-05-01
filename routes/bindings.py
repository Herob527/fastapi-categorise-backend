from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from typing import Annotated, List
from pydantic.types import UUID4
from sqlalchemy.orm import Session
from uuid import uuid4
from database_handle.database import get_db
from database_handle.models.bindings import BindingModel, Binding
from database_handle.models.categories import Category
from database_handle.queries.bindings import (
    get_one_binding,
    create_binding as create_new_binding,
    get_total_bindings,
    get_paginated_bindings as paginated_bindings_query,
    get_all_bindings as all_bindings_query,
    remove_binding as binding_remove,
    update_binding_category,
)
from database_handle.queries.categories import (
    create_category,
    get_one_category,
)
from routes.audios import post_new_audio
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


@router.get("", response_model=List[BindingModel])
def get_paginated_bindings(
    page: int = 0, per_page: int = 10, db: Session = Depends(get_db)
):
    if page < 0:
        raise HTTPException(
            status_code=400, detail="Page must be greater than or equal 0"
        )
    if per_page <= 0:
        raise HTTPException(status_code=400, detail="Page size must be greater than 0")
    return paginated_bindings_query(page=page, limit=per_page, db=db)


@router.get("/all", response_model=List[BindingModel])
def get_all_bindings(db: Session = Depends(get_db), category: str | None = None):
    return all_bindings_query(db, category)


@router.get("/{binding_id}", response_model=BindingModel)
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
    category_id = uuid4() if category_exist is None else category_exist.id
    new_binding = Binding(
        id=binding_id, category_id=category_id, audio_id=binding_id, text_id=binding_id
    )
    new_category = Category(id=category_id, name=category)
    try:

        await post_new_audio(id=binding_id, file=audio, db=db, commit=False)
        await post_new_text(id=binding_id, text="", db=db, commit=False)
        create_new_binding(db=db, binding=new_binding)
        create_category(db=db, category=new_category)
        db.commit()
    except HTTPException as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"Test": category}


@router.delete("/{binding_id}")
def remove_binding(binding_id: UUID4, db: Session = Depends(get_db)):
    binding_remove(db, binding_id)
    return {"hejo": binding_id}


@router.put("/{binding_id}/category_assign/{category_id}")
def binding_category_update(
    binding_id: UUID4, category_id: UUID4, db: Session = Depends(get_db)
):
    update_binding_category(binding_id, category_id, db)
    return {"hejo": binding_id, "hejo2": category_id}
