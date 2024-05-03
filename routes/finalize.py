from collections.abc import Callable
from pathlib import Path
from typing import overload
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database_handle.database import get_db
from shutil import copy2

from database_handle.queries.bindings import get_all_bindings
from database_handle.queries.categories import get_all_categories

__all__ = ["router"]

output_dir = Path("output")


class FinaliseConfigModel(BaseModel):
    omit_empty: bool = True
    line_format: str = "{file}|{text}"
    divide_by_category: bool = True
    export_transcript: bool = True


def prepare_path(dir: str):
    path = Path(dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_file(
    source_file: str,
    target_file: str,
):
    copy2(source_file, target_file)


def write_transcript(
    lines: list[str],
    target_file: str,
    filter_predicate: Callable[[str], bool] = lambda _: True,
):
    with open(target_file, "w", encoding="utf-8") as f:
        f.writelines(filter(filter_predicate, lines))


router = APIRouter(
    tags=["Finalise"],
    prefix="/finalise",
    responses={404: {"description": "Not found"}},
)


def prepare_structure(entries: list[str]):
    for entry in entries:
        path = Path(output_dir, entry)
        path.mkdir(parents=True, exist_ok=True)


@router.post("/")
def finalise(config: FinaliseConfigModel, db: Session = Depends(get_db)):
    bindings, result = get_all_bindings(db)
    for binding in bindings:
        result
        category = binding[1]
        
