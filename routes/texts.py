from fastapi import APIRouter, Depends, Form
from pydantic import UUID4
from sqlalchemy.orm import Session

from database_handle.database import get_db
from database_handle.models.texts import Texts
from database_handle.queries.texts import create_text

__all__ = ["router"]

router = APIRouter(
    tags=["Texts"],
    prefix="/texts",
    responses={404: {"description": "Not found"}},
)


@router.get("/{text_id}")
async def get_text(text_id: int):
    print(f"Got text with ID: {text_id}")
    return {"test": text_id}


@router.get("/")
async def get_all_texts():
    print("Got all texts")
    return {"test": "test"}


@router.post("/")
async def post_new_text(id: UUID4, text: str = Form(), db: Session = Depends(get_db)):
    new_text = Texts(id=id, text=text)
    create_text(db=db, text=new_text)
    return {"test": "test"}


@router.patch("/{text_id}")
async def update_text(text_id: UUID4, new_text: str = Form()):
    print("Updated text with name: {text_id}")
    return {"test": text_id}


@router.delete("/{text_id}")
async def remove_text(text_id: UUID4):
    print(f"Removed text with ID: {text_id}")
    return {"test": text_id}
