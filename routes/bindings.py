from typing import Annotated, List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic.types import UUID4
from sqlalchemy.orm import Session

from database_handle.database import get_db
from database_handle.models.bindings import Binding, BindingModel, PaginatedBindingModel
from database_handle.models.categories import Category
from database_handle.queries.bindings import (
    create_binding as create_new_binding,
    get_pagination,
)
from database_handle.queries.bindings import (
    get_all_bindings as all_bindings_query,
)
from database_handle.queries.bindings import (
    get_one_binding,
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


@router.get("", response_model=PaginatedBindingModel)
def get_paginated_bindings(
    page: int = 0, per_page: int = 10, db: Session = Depends(get_db)
):
    if page < 0:
        raise HTTPException(
            status_code=400, detail="Page must be greater than or equal 0"
        )
    if per_page <= 0:
        raise HTTPException(status_code=400, detail="Page size must be greater than 0")
    pagination = get_pagination(db)

    bindings = paginated_bindings_query(page=page, limit=per_page, db=db)
    return PaginatedBindingModel(
        bindings=bindings,
        page=page,
        pagination=pagination,
    )


@router.get("/all", response_model=List[BindingModel])
def get_all_bindings(db: Session = Depends(get_db), category: str | None = None):
    return all_bindings_query(db, category)


@router.get("/{binding_id}", response_model=BindingModel)
def get_binding(binding_id: str, db: Session = Depends(get_db)):
    return get_one_binding(db, binding_id)


class Exists(str):
    EXISTS = "EXISTS"
    NOT_EXISTS = "NOT_EXISTS"

def make_category_data(category_name: str | None, db: Session):
    if category_name is None:
        return (None, Exists.EXISTS)
    existing_category = get_one_category_by_name(db=db, name=category_name)
    if existing_category is not None:
        return (existing_category, Exists.EXISTS)
    return (Category(id=uuid4(),name=category_name), Exists.NOT_EXISTS)

@router.post("")
async def create_binding(
    audio: Annotated[UploadFile, File()],
    category: str | None = None,
    db: Session = Depends(get_db),
):
    binding_id = uuid4()
    category_data = make_category_data(category, db)
    new_binding = Binding(
        id=binding_id, category_id=category_id if category is not None else None, audio_id=binding_id, text_id=binding_id
    )
    new_category = (
        Category(id=category_id, name=category) if category is not None else None
    )
    try:
        if category_data[1] == "NOT_EXISTS":
            create_category(db=db, category=category_data[0])
        await post_new_audio(id=binding_id, file=audio, db=db, commit=False)
        await post_new_text(id=binding_id, text="", db=db, commit=False)
        create_new_binding(db=db, binding=new_binding)
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


@router.put("/{binding_id}/remove_category")
def binding_category_remove(binding_id: UUID4, db: Session = Depends(get_db)):
    update_binding_category(binding_id, None, db)
