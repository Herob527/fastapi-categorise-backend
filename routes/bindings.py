from fastapi import APIRouter, Depends, File, Form, UploadFile
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4
from database_handle.database import get_db
from database_handle.queries.bindings import get_one_binding

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
    print(binding_id)
    await post_new_audio(id=binding_id, file=audio, db=db)
    await post_new_text(text=text, db=db)
    await post_new_category(category)
    return {"Test": category}


@router.delete("/{binding_id}")
def remove_binding(binding_id: int):
    print(f"Removed binding with id {binding_id}")
    return {"hejo": binding_id}
