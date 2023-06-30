from fastapi import APIRouter, Depends, File, Form, UploadFile
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4
from database_handle.database import get_db
from database_handle.models.bindings import Bindings
from database_handle.queries.bindings import (
    get_one_binding,
    create_binding as create_new_binding,
)
import asyncio
from routes.audios import post_new_audio
from routes.categories import post_new_category
from routes.texts import post_new_text

__all__ = ["router"]

router = APIRouter(
    tags=["Bindings"],
    prefix="/bindings",
    responses={404: {"description": "Not found"}},
)


@router.get("")
def get_all_bindings():
    return {"hejo", "hejo"}


@router.get("/{binding_id}")
def get_binding(binding_id: str, db: Session = Depends(get_db)):
    return get_one_binding(db, binding_id)


@router.post("")
async def create_binding(
    audio: Annotated[UploadFile, File()],
    category: str = Form(),
    text: str = Form(),
    db: Session = Depends(get_db),
):
    binding_id = uuid4()
    new_binding = Bindings(
        id=binding_id, category_id=binding_id, audio_id=binding_id, text_id=binding_id
    )
    try:
        done, cancel, result = await asyncio.gather(
            post_new_audio(id=binding_id, file=audio, db=db),
            post_new_category(id=binding_id, category=category, db=db),
            post_new_text(id=binding_id, text=text, db=db),
        )
    except Exception as e:
        db.rollback()
        return
    create_new_binding(db=db, binding=new_binding)
    db.commit()
    return {"Test": category}


@router.delete("/{binding_id}")
def remove_binding(binding_id: int):
    print(f"Removed binding with id {binding_id}")
    return {"hejo": binding_id}
