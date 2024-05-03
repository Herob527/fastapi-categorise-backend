from collections.abc import Callable, Sequence
from pathlib import Path
from shutil import copy2, rmtree
from typing import Dict, Tuple, TypedDict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Row
from sqlalchemy.orm import Session

from database_handle.database import get_db
from database_handle.models.audios import Audio
from database_handle.models.bindings import Binding
from database_handle.models.categories import Category
from database_handle.models.texts import Text
from database_handle.queries.bindings import get_all_bindings

__all__ = ["router"]

output_dir = Path("output")


class FinaliseConfigModel(BaseModel):
    omit_empty: bool = True
    line_format: str = "{file}|{text}"
    divide_by_category: bool = True
    export_transcript: bool = True
    uncaterized_name: str = "Uncategorized"


def prepare_path(dir: str):
    path = Path(output_dir, dir, "wavs")
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
    with open(target_file, "a", encoding="utf-8") as f:
        f.writelines(filter(filter_predicate, lines))


router = APIRouter(
    tags=["Finalise"],
    prefix="/finalise",
    responses={404: {"description": "Not found"}},
)

type BindingEntry = Row[Tuple[Binding, Category, Audio, Text]]


def process_path(_binding: BindingEntry, config: FinaliseConfigModel):
    _, category, audio, _ = _binding.tuple()

    target_dir = (
        Path(
            output_dir,
            str(category.name) if category is not None else config.uncaterized_name,
        )
        if config.divide_by_category
        else output_dir
    )

    output_file = Path(target_dir, "wavs", str(audio.file_name))
    source_file = Path(str(audio.url))

    return [source_file, output_file]


class TranscriptEntry(TypedDict):
    lines: list[str]
    path: Path


def process_transcript(bindings: Sequence[BindingEntry], config: FinaliseConfigModel):
    res: Dict[str, TranscriptEntry] = dict()
    for binding in bindings:
        _, category, audio, text = binding.tuple()
        target_dir = (
            Path(
                output_dir,
                str(category.name) if category is not None else config.uncaterized_name,
            )
            if config.divide_by_category
            else output_dir
        )

        output_file = Path(target_dir, "transcript.txt")
        current_category = (
            str(category.name) if category is not None else config.uncaterized_name
        )

        current_value = res.get(current_category)
        text_to_insert = f"{audio.file_name}|{text.text}\n"
        if current_value is None:
            res[current_category] = {
                "lines": [text_to_insert],
                "path": output_file,
            }
        else:
            res[current_category]["lines"].append(text_to_insert)

    return res.values()


@router.post("/")
def finalise(config: FinaliseConfigModel, db: Session = Depends(get_db)):
    rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir()
    bindings = get_all_bindings(db)
    categories = (
        map(
            lambda x: (
                str(x.tuple()[1].name) if x.tuple()[1] else config.uncaterized_name
            ),
            bindings,
        )
        if config.divide_by_category
        else map(lambda _: "All", ["all"])
    )
    audio_paths = map(lambda x: process_path(x, config), bindings)

    transcript_data = process_transcript(bindings, config)

    for category in categories:
        prepare_path(category)

    for audio_path in audio_paths:
        copy_file(str(audio_path[0]), str(audio_path[1]))

    for data in transcript_data:
        write_transcript(
            data["lines"],
            str(data["path"]),
            lambda x: not x.strip().endswith("|") if config.omit_empty else True,
        )
