from fastapi import APIRouter, File, Form, UploadFile
from typing import Annotated
from pydantic import BaseModel

__all__ = ["router"]

router = APIRouter(
    tags=["Bindings"],
    prefix="/bindings",
    responses={404: {"description": "Not found"}},
)


@router.get("")
def get_all_bindings():
    return {"hejo", "hejo"}


@router.get("{binding_id}")
def get_binding(binding_id: int):
    print(f"Got binding with id {binding_id}")
    return {"hejo": binding_id}


class PostRequest(BaseModel):
    category: str
    text: str


class Category(BaseModel):
    name: str


@router.post("")
def create_binding(
    audio: Annotated[UploadFile, Form()],
    category: str = Form(),
    text: str = Form(),
):
    return {"Test": category}


@router.delete("{binding_id}")
def remove_binding(binding_id: int):
    print(f"Removed binding with id {binding_id}")
    return {"hejo": binding_id}
