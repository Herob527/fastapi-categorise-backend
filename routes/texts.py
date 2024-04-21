from fastapi import APIRouter, Depends, Form
from pydantic import UUID4
from sqlalchemy.orm import Session

from database_handle.database import get_db
from database_handle.models.texts import Text, TextModel
from database_handle.queries.texts import (
    create_text,
    get_one_text,
    update_text as text_update,
)

__all__ = ["router"]

router = APIRouter(
    tags=["Texts"],
    prefix="/texts",
    responses={404: {"description": "Not found"}},
)


@router.get("/{text_id}", response_model=TextModel)
async def get_text(text_id: UUID4, db: Session = Depends(get_db)):
    resp = get_one_text(db, text_id)
    return resp


@router.get("/")
async def get_all_texts():
    print("Got all texts")
    return {"test": "test"}


@router.post("/")
async def post_new_text(
    id: UUID4, text: str = Form(), db: Session = Depends(get_db), commit=True
):
    new_text = Text(id=id, text=text)
    create_text(db=db, text=new_text)
    if commit:
        db.commit()
    return {"test": "test"}


@router.patch("/{text_id}")
async def update_text(
    text_id: UUID4, new_text: str, db: Session = Depends(get_db)
) -> None:
    text_update(db, Text(id=text_id, text=new_text))
    return None


@router.delete("/{text_id}")
async def remove_text(text_id: UUID4):
    print(f"Removed text with ID: {text_id}")
    return {"test": text_id}
